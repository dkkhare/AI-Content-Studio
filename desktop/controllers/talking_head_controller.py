from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtCore import QObject, QThread, Signal, Slot

from backend.talking_head import BookImporter, TalkingHeadPreflight, plan_episodes
from desktop.workers.talking_head_worker import TalkingHeadWorker


class TalkingHeadController(QObject):
    generationStarted = Signal()
    generationProgress = Signal(float, str)
    generationFinished = Signal(object)
    generationFailed = Signal(str)
    generationCancelled = Signal()

    def __init__(
        self,
        parent=None,
        *,
        worker_factory: Callable[[], TalkingHeadWorker] = TalkingHeadWorker,
        importer=None,
        preflight=None,
    ):
        super().__init__(parent)
        self.worker_factory = worker_factory
        self.importer = importer or BookImporter()
        self.preflight_service = preflight or TalkingHeadPreflight()
        self.project = None
        self.thread = None
        self.worker = None
        self._running = False

    def set_project(self, project):
        if self._running:
            raise RuntimeError("Cannot change project during series generation.")
        self.project = project
        if project is None:
            return {"output_directory": "", "work_directory": ""}
        root = Path(project.root).resolve()
        return {
            "output_directory": str(root / "output" / "talking-head-series"),
            "work_directory": str(root / "output" / ".talking-head-work"),
        }

    def preview(self, book, *, episode_minutes=15.0, words_per_minute=140.0):
        imported = self.importer.import_book(book)
        plan = plan_episodes(
            imported.blocks,
            target_minutes=episode_minutes,
            words_per_minute=words_per_minute,
        )
        return imported, plan

    def preflight(self, **settings):
        return self.preflight_service.run(
            sadtalker_directory=settings["sadtalker_directory"],
            sadtalker_python=settings["sadtalker_python"],
            output_directory=settings["output_directory"],
            size=settings.get("size", 256),
            enhancer=settings.get("enhancer", ""),
        )

    def start(self, **settings):
        if self._running:
            raise RuntimeError("Talking-head series generation is already active.")
        if self.project is None:
            raise RuntimeError("Open a project before generating a series.")
        root = Path(self.project.root).resolve()
        for key in ("output_directory", "work_directory"):
            path = Path(settings[key]).resolve()
            if path != root and root not in path.parents:
                raise ValueError("Talking-head outputs must remain inside the project.")
        thread = QThread(self)
        worker = self.worker_factory()
        worker.configure(**settings)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.started.connect(self.generationStarted)
        worker.progress.connect(self.generationProgress)
        worker.finished.connect(self._finished)
        worker.failed.connect(self._failed)
        worker.cancelled.connect(self._cancelled)
        for signal in (worker.finished, worker.failed, worker.cancelled):
            signal.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._clear)
        self.thread, self.worker, self._running = thread, worker, True
        self.project.start_processing("talking-head-series")
        thread.start()

    @Slot(object)
    def _finished(self, result):
        manifest = str(result.manifest)
        self.project.register_asset("talking_head_series_manifest", manifest)
        self.project.complete_processing()
        self._running = False
        self.generationFinished.emit(result)

    @Slot(str)
    def _failed(self, message):
        self.project.set_error(message)
        self._running = False
        self.generationFailed.emit(message)

    @Slot()
    def _cancelled(self):
        self.project.reset_processing()
        self._running = False
        self.generationCancelled.emit()

    @Slot()
    def _clear(self):
        self.thread = None
        self.worker = None
        self._running = False

    def cancel(self):
        if self.worker is not None:
            self.worker.request_cancel()

    def is_running(self):
        return self._running

    def cleanup(self):
        self.cancel()
        if self.thread is not None and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait(5000)
        self.thread = None
        self.worker = None
        self._running = False
