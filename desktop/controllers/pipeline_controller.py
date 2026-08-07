from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from backend.pipeline import (
    PipelineContext,
    PipelineRunner,
    ProcessingPipeline,
    build_project_pipeline,
)
from backend.video import FFmpegRenderer


class PipelineController(QObject):
    """Qt bridge for background project processing."""

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
        self.translator = None

    @property
    def running(self) -> bool:
        return self.runner.running

    @property
    def is_paused(self) -> bool:
        return self.runner.paused

    @property
    def project(self):
        return self.context.project if self.context is not None else None

    def set_translator(self, translator) -> None:
        if self.running:
            raise RuntimeError("Cannot change translator while processing is running.")
        self.translator = translator

    def set_pipeline(self, pipeline: ProcessingPipeline) -> None:
        if self.running:
            raise RuntimeError("Cannot replace pipeline while processing is running.")
        self.runner = PipelineRunner(pipeline)

    def configure_project(self, project) -> ProcessingPipeline:
        if self.running:
            raise RuntimeError("Cannot configure pipeline while processing is running.")

        renderer = None
        if bool(project.get_setting("pipeline_video_enabled", False)):
            renderer = FFmpegRenderer(
                ffmpeg_path=str(project.get_setting("ffmpeg_path", "")) or None,
                fps=int(project.get_setting("video_fps", 30)),
                seconds_per_image=float(project.get_setting("video_seconds_per_image", 3.0)),
            )

        pipeline = build_project_pipeline(
            project,
            translator=self.translator,
            renderer=renderer,
        )
        self.set_pipeline(pipeline)
        return pipeline

    def clear_stages(self) -> None:
        if self.running:
            raise RuntimeError("Cannot clear stages while processing is running.")
        self.runner.pipeline.clear()

    def add_stage(self, stage):
        if self.running:
            raise RuntimeError("Cannot add stages while processing is running.")
        return self.runner.add_stage(stage)

    def start_project(self, project, *, data=None, resume: bool = True, configure: bool = True) -> bool:
        if self.running:
            return False

        if configure:
            self.configure_project(project)

        self.context = PipelineContext(project, data=data)
        project.clear_error()
        project.set_status("processing")
        project.set_progress(0)
        self.started.emit()

        self.runner.start(
            self.context,
            progress_callback=self._progress,
            finished_callback=self._finished,
            error_callback=self._failed,
            resume=resume,
        )
        return True

    def pause(self) -> bool:
        if not self.runner.pause():
            return False
        if self.project is not None:
            self.project.set_status("paused")
        self.paused.emit()
        return True

    def resume(self) -> bool:
        if not self.runner.resume():
            return False
        if self.project is not None:
            self.project.set_status("processing")
        self.resumed.emit()
        return True

    def cancel(self) -> bool:
        if not self.runner.cancel():
            return False
        return True

    def wait(self, timeout: float | None = None) -> bool:
        return self.runner.wait(timeout)

    def _progress(self, progress) -> None:
        if self.project is not None:
            self.project.set_status(str(getattr(progress, "status", "processing")))
            self.project.set_progress(int(getattr(progress, "percent", 0)))
        self.progressChanged.emit(progress)

    def _finished(self, state) -> None:
        status = str(getattr(state, "status", ""))
        if status == "cancelled":
            if self.project is not None:
                self.project.set_status("cancelled")
            self.cancelled.emit()
            return

        if self.project is not None:
            self.project.set_status("completed")
            self.project.set_progress(100)
            self.project.clear_error()
        self.completed.emit(state)

    def _failed(self, error: Exception) -> None:
        if self.project is not None:
            self.project.set_error(str(error))
        self.failed.emit(str(error))

    def reset(self) -> None:
        if self.running:
            raise RuntimeError("Cannot reset while processing is running.")
        self.context = None
