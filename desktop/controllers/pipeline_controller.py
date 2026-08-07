from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from backend.pipeline import PipelineContext, PipelineRunner, ProcessingPipeline


class PipelineController(QObject):
    """Qt bridge for the Milestone 12 background processing pipeline."""

    started = Signal()
    progressChanged = Signal(object)
    paused = Signal()
    resumed = Signal()
    cancelled = Signal()
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.runner = PipelineRunner(ProcessingPipeline())
        self.context: PipelineContext | None = None

    @property
    def running(self) -> bool:
        return self.runner.running

    @property
    def is_paused(self) -> bool:
        return self.runner.paused

    def set_pipeline(self, pipeline: ProcessingPipeline) -> None:
        if self.running:
            raise RuntimeError("Cannot replace pipeline while processing is running.")
        self.runner = PipelineRunner(pipeline)

    def clear_stages(self) -> None:
        if self.running:
            raise RuntimeError("Cannot clear stages while processing is running.")
        self.runner.pipeline.clear()

    def add_stage(self, stage):
        if self.running:
            raise RuntimeError("Cannot add stages while processing is running.")
        return self.runner.add_stage(stage)

    def start_project(self, project, *, data=None, resume: bool = True) -> bool:
        if self.running:
            return False

        self.context = PipelineContext(project, data=data)
        self.started.emit()

        self.runner.start(
            self.context,
            progress_callback=self.progressChanged.emit,
            finished_callback=self._finished,
            error_callback=self._failed,
            resume=resume,
        )
        return True

    def pause(self) -> bool:
        if not self.runner.pause():
            return False
        self.paused.emit()
        return True

    def resume(self) -> bool:
        if not self.runner.resume():
            return False
        self.resumed.emit()
        return True

    def cancel(self) -> bool:
        if not self.runner.cancel():
            return False
        self.cancelled.emit()
        return True

    def wait(self, timeout: float | None = None) -> bool:
        return self.runner.wait(timeout)

    def _finished(self, state) -> None:
        if getattr(state, "status", "") == "cancelled":
            self.cancelled.emit()
        else:
            self.completed.emit(state)

    def _failed(self, error: Exception) -> None:
        self.failed.emit(str(error))
