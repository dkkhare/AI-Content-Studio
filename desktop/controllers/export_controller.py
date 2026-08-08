from __future__ import annotations

from pathlib import Path
from threading import Event

from PySide6.QtCore import QObject, QThread, Signal, Slot

from backend.exporting import (
    BatchExportQueue,
    BatchExportRunner,
    ExportCancelled,
    ProjectExportService,
)
from backend.project.serializer import ProjectSerializer


class _ExportWorker(QObject):
    progress = Signal(float)
    finished = Signal(object, str)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, service, project, destination, preset, cancel_event):
        super().__init__()
        self.service = service
        self.project = project
        self.destination = destination
        self.preset = preset
        self.cancel_event = cancel_event

    @Slot()
    def run(self):
        try:
            manifest, output = self.service.export(
                self.project,
                self.destination,
                self.preset,
                progress=self.progress.emit,
                cancel_event=self.cancel_event,
            )
            self.finished.emit(manifest, str(output))
        except ExportCancelled:
            self.cancelled.emit()
        except Exception as exc:
            self.failed.emit(str(exc))


class _BatchWorker(QObject):
    jobChanged = Signal(object)
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, runner, cancel_event):
        super().__init__()
        self.runner = runner
        self.cancel_event = cancel_event

    @Slot()
    def run(self):
        try:
            self.runner.run_pending(
                cancel_event=self.cancel_event,
                on_job=self.jobChanged.emit,
            )
            self.finished.emit(tuple(self.runner.queue.jobs))
        except Exception as exc:
            self.failed.emit(str(exc))


class ExportDesktopController(QObject):
    """Project-aware single and persistent batch export facade."""

    exportStarted = Signal()
    exportProgress = Signal(float)
    exportFinished = Signal(object, str)
    exportFailed = Signal(str)
    exportCancelled = Signal()
    batchStarted = Signal()
    batchJobChanged = Signal(object)
    batchFinished = Signal(object)
    batchFailed = Signal(str)

    def __init__(self, parent=None, *, service=None, project_loader=None):
        super().__init__(parent)
        self.service = service or ProjectExportService()
        self.project_loader = project_loader or ProjectSerializer.load
        self.project = None
        self.queue = None
        self._thread = None
        self._worker = None
        self._cancel_event = None

    def set_project(self, project):
        if self.is_running():
            raise RuntimeError("Cannot change project while export is active.")
        self.project = project
        self.queue = (
            BatchExportQueue.load(self._queue_path(project))
            if project is not None
            else None
        )
        return self.context()

    @staticmethod
    def _queue_path(project):
        return Path(project.root) / "output" / "export_queue.json"

    def presets(self):
        return tuple(sorted(self.service.presets))

    @staticmethod
    def _safe_name(value):
        name = "".join(
            character.lower() if character.isalnum() else "-"
            for character in str(value).strip()
        )
        while "--" in name:
            name = name.replace("--", "-")
        return name.strip("-") or "project"

    def default_destination(self, preset="publishing", parent=None):
        if self.project is None:
            return ""
        base = Path(parent) if parent else Path(self.project.root) / "exports"
        return str(
            (base / f"{self._safe_name(self.project.name)}-{preset}").resolve()
        )

    def context(self):
        return {
            "presets": self.presets(),
            "destination": self.default_destination(),
            "jobs": self.queue_rows(),
        }

    def preview(self, preset="publishing"):
        if self.project is None:
            raise RuntimeError("Open a project before previewing export.")
        selected, sources = self.service.collect(self.project, preset)
        required = set(selected.required)
        return [
            {
                "role": role,
                "path": str(source),
                "size": source.stat().st_size,
                "required": role in required,
            }
            for role, source in sources
        ]

    def export_sync(self, destination, preset="publishing", progress=None):
        if self.project is None:
            raise RuntimeError("Open a project before exporting.")
        return self.service.export(
            self.project, destination, preset, progress=progress
        )

    def _start_thread(self, worker, terminal_signals):
        self._cancel_event = getattr(worker, "cancel_event", Event())
        self._thread = QThread(self)
        self._worker = worker
        worker.moveToThread(self._thread)
        self._thread.started.connect(worker.run)
        for signal in terminal_signals:
            signal.connect(self._thread.quit)
        self._thread.finished.connect(worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._clear_worker)
        self._thread.start()

    def start_export(self, destination, preset="publishing"):
        if self.project is None:
            raise RuntimeError("Open a project before exporting.")
        if self.is_running():
            raise RuntimeError("Project export is already active.")
        self.service.collect(self.project, preset)
        cancel_event = Event()
        worker = _ExportWorker(
            self.service, self.project, destination, preset, cancel_event
        )
        worker.progress.connect(self.exportProgress)
        worker.finished.connect(self.exportFinished)
        worker.failed.connect(self.exportFailed)
        worker.cancelled.connect(self.exportCancelled)
        self._start_thread(
            worker, (worker.finished, worker.failed, worker.cancelled)
        )
        self.exportStarted.emit()

    def enqueue_current(
        self, destination, preset="publishing", *, mode="export"
    ):
        if self.project is None or self.queue is None:
            raise RuntimeError("Open a project before queueing export.")
        self.service.collect(self.project, preset)
        ProjectSerializer.save(self.project)
        job = self.queue.enqueue(
            self.project.root, destination, preset, mode=mode
        )
        self.batchJobChanged.emit(job)
        return job

    def queue_rows(self):
        if self.queue is None:
            return []
        return [
            {
                "id": job.id,
                "project": Path(job.project_root).name,
                "preset": job.preset,
                "mode": job.mode,
                "phase": job.phase,
                "destination": job.destination,
                "status": job.status,
                "attempts": job.attempts,
                "error": job.error,
            }
            for job in self.queue.jobs
        ]

    def retry_job(self, job_id):
        if self.queue is None:
            raise RuntimeError("Open a project before retrying export.")
        job = self.queue.retry(job_id)
        self.batchJobChanged.emit(job)
        return job

    def start_batch(self):
        if self.queue is None:
            raise RuntimeError("Open a project before running batch export.")
        if self.is_running():
            raise RuntimeError("An export operation is already active.")
        if not any(job.status == "pending" for job in self.queue.jobs):
            raise ValueError("There are no pending export jobs.")
        cancel_event = Event()
        runner = BatchExportRunner(
            self.queue,
            service=self.service,
            project_loader=self.project_loader,
        )
        worker = _BatchWorker(runner, cancel_event)
        worker.jobChanged.connect(self.batchJobChanged)
        worker.finished.connect(self.batchFinished)
        worker.failed.connect(self.batchFailed)
        self._start_thread(worker, (worker.finished, worker.failed))
        self.batchStarted.emit()

    @Slot()
    def _clear_worker(self):
        self._worker = None
        self._thread = None
        self._cancel_event = None

    def cancel(self):
        if self._cancel_event is not None:
            self._cancel_event.set()

    def is_running(self):
        return self._thread is not None and self._thread.isRunning()

    def cleanup(self):
        self.cancel()
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait(5000)
