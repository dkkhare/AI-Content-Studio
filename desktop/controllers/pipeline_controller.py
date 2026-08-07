from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from backend.pipeline import (
    PipelineContext,
    PipelineJobQueue,
    PipelineRunner,
    ProcessingPipeline,
    build_project_pipeline,
)
from backend.project.serializer import ProjectSerializer
from backend.video import FFmpegRenderer


class PipelineController(QObject):
    """Qt bridge for direct and queued background project processing."""

    started = Signal()
    progressChanged = Signal(object)
    paused = Signal()
    resumed = Signal()
    cancelled = Signal()
    completed = Signal(object)
    failed = Signal(str)

    queueChanged = Signal(object)
    jobSubmitted = Signal(object)
    jobUpdated = Signal(object)
    jobFinished = Signal(object)
    queueRecoveryError = Signal(str)

    def __init__(self, parent=None, queue_state_file: str | Path | None = None):
        super().__init__(parent)
        self.runner = PipelineRunner(ProcessingPipeline())
        self.context: PipelineContext | None = None
        self.translator = None

        state_file = queue_state_file or (
            Path.home() / ".ai-content-studio" / "processing_queue.json"
        )
        self.job_queue = PipelineJobQueue(state_file=state_file)

    @property
    def running(self) -> bool:
        return self.runner.running

    @property
    def is_paused(self) -> bool:
        return self.runner.paused

    @property
    def project(self):
        return self.context.project if self.context is not None else None

    @property
    def queue_running(self) -> bool:
        current = self.job_queue.current
        return bool(current and current.status in {"running", "paused"})

    def queue_records(self) -> list[dict]:
        return self.job_queue.records()

    def set_translator(self, translator) -> None:
        if self.running or self.queue_running:
            raise RuntimeError("Cannot change translator while processing is running.")
        self.translator = translator

    def _renderer_for_project(self, project):
        if not bool(project.get_setting("pipeline_video_enabled", False)):
            return None
        return FFmpegRenderer(
            ffmpeg_path=str(project.get_setting("ffmpeg_path", "")) or None,
            fps=int(project.get_setting("video_fps", 30)),
            seconds_per_image=float(project.get_setting("video_seconds_per_image", 3.0)),
        )

    def _pipeline_for_project(self, project) -> ProcessingPipeline:
        return build_project_pipeline(
            project,
            translator=self.translator,
            renderer=self._renderer_for_project(project),
        )

    def set_pipeline(self, pipeline: ProcessingPipeline) -> None:
        if self.running:
            raise RuntimeError("Cannot replace pipeline while processing is running.")
        self.runner = PipelineRunner(pipeline)

    def configure_project(self, project) -> ProcessingPipeline:
        if self.running:
            raise RuntimeError("Cannot configure pipeline while processing is running.")
        pipeline = self._pipeline_for_project(project)
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

    # --------------------------------------------------
    # Direct execution
    # --------------------------------------------------

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
        return bool(self.runner.cancel())

    def wait(self, timeout: float | None = None) -> bool:
        return self.runner.wait(timeout)

    # --------------------------------------------------
    # Queue execution
    # --------------------------------------------------

    def submit_project(
        self,
        project,
        *,
        data=None,
        priority: int = 0,
        resume: bool = True,
        job_id: str | None = None,
    ):
        pipeline = self._pipeline_for_project(project)
        context = PipelineContext(project, data=data)
        runner = PipelineRunner(pipeline)

        project.clear_error()
        project.set_status("queued")
        project.set_progress(0)
        self._save_project_quietly(project)

        job = self.job_queue.submit(
            context,
            runner,
            priority=priority,
            progress_callback=self._queue_progress,
            finished_callback=self._queue_finished,
            error_callback=self._queue_failed,
            resume=resume,
            job_id=job_id,
        )
        self.jobSubmitted.emit(job.to_dict())
        self._emit_queue_changed()
        return job

    def pause_queue(self) -> bool:
        result = self.job_queue.pause_current()
        if result:
            current = self.job_queue.current
            if current is not None:
                current.context.project.set_status("paused")
                self._save_project_quietly(current.context.project)
                self.jobUpdated.emit(current.to_dict())
            self._emit_queue_changed()
        return result

    def resume_queue(self) -> bool:
        result = self.job_queue.resume_current()
        if result:
            current = self.job_queue.current
            if current is not None:
                current.context.project.set_status("processing")
                self._save_project_quietly(current.context.project)
                self.jobUpdated.emit(current.to_dict())
            self._emit_queue_changed()
        return result

    def cancel_job(self, job_id: str) -> bool:
        result = self.job_queue.cancel_job(str(job_id))
        if result:
            job = self.job_queue.get(str(job_id))
            if job is not None:
                if job.status == "cancelled":
                    job.context.project.set_status("cancelled")
                    self._save_project_quietly(job.context.project)
                self.jobUpdated.emit(job.to_dict())
            self._emit_queue_changed()
        return result

    def retry_job(self, job_id: str):
        metadata = next(
            (
                item
                for item in self.queue_records()
                if str(item.get("job_id", "")) == str(job_id)
            ),
            None,
        )
        if metadata is None or metadata.get("status") not in {"failed", "cancelled"}:
            return None

        root = Path(str(metadata.get("project_root", ""))).expanduser()
        project = ProjectSerializer.load(root)
        project.root = root.resolve()
        return self.submit_project(
            project,
            data=dict(metadata.get("data") or {}),
            priority=int(metadata.get("priority", 0)),
            resume=True,
        )

    def recover_pending_jobs(self) -> int:
        recovered = 0
        records = list(self.job_queue.persisted_jobs())
        for metadata in records:
            if metadata.get("status") not in {"queued", "running", "paused", "interrupted"}:
                continue
            try:
                root = Path(str(metadata.get("project_root", ""))).expanduser()
                project = ProjectSerializer.load(root)
                project.root = root.resolve()
                self.submit_project(
                    project,
                    data=dict(metadata.get("data") or {}),
                    priority=int(metadata.get("priority", 0)),
                    resume=True,
                    job_id=str(metadata.get("job_id") or "") or None,
                )
                recovered += 1
            except Exception as exc:
                self.queueRecoveryError.emit(
                    f"Unable to recover queued job {metadata.get('job_id', '')}: {exc}"
                )
        self._emit_queue_changed()
        return recovered

    def shutdown_queue(self, cancel_current: bool = True, wait: float | None = 5.0) -> None:
        self.job_queue.shutdown(cancel_current=cancel_current, wait=wait)
        self._emit_queue_changed()

    def _queue_progress(self, job, progress) -> None:
        project = job.context.project
        project.set_status(str(getattr(progress, "status", "processing")))
        project.set_progress(int(getattr(progress, "percent", 0)))
        # Qt signals are safe to emit from the queue worker; receivers in the
        # GUI thread are delivered through Qt's queued connection semantics.
        # Reuse the existing stage-level monitor for queued processing too.
        self.progressChanged.emit(progress)
        self.jobUpdated.emit(job.to_dict())
        self.queueChanged.emit(self.queue_records())

    def _queue_finished(self, job) -> None:
        project = job.context.project
        if job.status == "cancelled":
            project.set_status("cancelled")
        else:
            project.set_status("completed")
            project.set_progress(100)
            project.clear_error()
        self._save_project_quietly(project)
        self.jobFinished.emit(job.to_dict())
        self._emit_queue_changed()

    def _queue_failed(self, job, error: Exception) -> None:
        project = job.context.project
        project.set_error(str(error))
        self._save_project_quietly(project)
        self.jobFinished.emit(job.to_dict())
        self._emit_queue_changed()

    def _emit_queue_changed(self) -> None:
        self.queueChanged.emit(self.queue_records())

    @staticmethod
    def _save_project_quietly(project) -> None:
        try:
            ProjectSerializer.save(project)
        except Exception:
            pass

    # --------------------------------------------------
    # Direct execution callbacks
    # --------------------------------------------------

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
            self._save_project_quietly(self.project)
        self.completed.emit(state)

    def _failed(self, error: Exception) -> None:
        if self.project is not None:
            self.project.set_error(str(error))
            self._save_project_quietly(self.project)
        self.failed.emit(str(error))

    def reset(self) -> None:
        if self.running:
            raise RuntimeError("Cannot reset while processing is running.")
        self.context = None
