from __future__ import annotations

from pathlib import Path
from threading import Event

from PySide6.QtCore import QObject, QThread, Signal, Slot

from backend.exporting import ExportCancelled, ProjectExportService


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


class ExportDesktopController(QObject):
    """Project-aware package preview and background export facade."""

    exportStarted = Signal()
    exportProgress = Signal(float)
    exportFinished = Signal(object, str)
    exportFailed = Signal(str)
    exportCancelled = Signal()

    def __init__(self, parent=None, *, service=None):
        super().__init__(parent)
        self.service = service or ProjectExportService()
        self.project = None
        self._thread = None
        self._worker = None
        self._cancel_event = None

    def set_project(self, project):
        if self.is_running():
            raise RuntimeError("Cannot change project while export is active.")
        self.project = project
        return self.context()

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

    def start_export(self, destination, preset="publishing"):
        if self.project is None:
            raise RuntimeError("Open a project before exporting.")
        if self.is_running():
            raise RuntimeError("Project export is already active.")
        self.service.collect(self.project, preset)
        self._cancel_event = Event()
        self._thread = QThread(self)
        self._worker = _ExportWorker(
            self.service,
            self.project,
            destination,
            preset,
            self._cancel_event,
        )
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self.exportProgress)
        self._worker.finished.connect(self.exportFinished)
        self._worker.failed.connect(self.exportFailed)
        self._worker.cancelled.connect(self.exportCancelled)
        for signal in (
            self._worker.finished,
            self._worker.failed,
            self._worker.cancelled,
        ):
            signal.connect(self._thread.quit)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._clear_worker)
        self._thread.start()
        self.exportStarted.emit()

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
