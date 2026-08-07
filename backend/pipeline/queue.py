from __future__ import annotations

import queue
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable
from uuid import uuid4

from .runner import PipelineRunner


@dataclass
class PipelineJob:
    context: object
    runner: PipelineRunner
    job_id: str = field(default_factory=lambda: uuid4().hex)
    status: str = "queued"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: str = ""
    finished_at: str = ""
    error: str = ""


class PipelineJobQueue:
    """Single-worker FIFO queue for long-running project processing jobs."""

    def __init__(self):
        self._queue: queue.Queue[PipelineJob | None] = queue.Queue()
        self._worker: threading.Thread | None = None
        self._stop = threading.Event()
        self._current: PipelineJob | None = None
        self._lock = threading.RLock()

    @property
    def current(self) -> PipelineJob | None:
        with self._lock:
            return self._current

    @property
    def running(self) -> bool:
        return self._worker is not None and self._worker.is_alive()

    def start(self) -> None:
        if self.running:
            return
        self._stop.clear()
        self._worker = threading.Thread(
            target=self._work,
            name="ai-content-studio-pipeline-queue",
            daemon=True,
        )
        self._worker.start()

    def submit(
        self,
        context,
        runner: PipelineRunner,
        *,
        progress_callback=None,
        finished_callback: Callable[[PipelineJob], None] | None = None,
        error_callback: Callable[[PipelineJob, Exception], None] | None = None,
        resume: bool = True,
    ) -> PipelineJob:
        job = PipelineJob(context=context, runner=runner)
        job._progress_callback = progress_callback
        job._finished_callback = finished_callback
        job._error_callback = error_callback
        job._resume = resume
        self._queue.put(job)
        self.start()
        return job

    def cancel_current(self) -> bool:
        job = self.current
        return bool(job and job.runner.cancel())

    def pause_current(self) -> bool:
        job = self.current
        return bool(job and job.runner.pause())

    def resume_current(self) -> bool:
        job = self.current
        return bool(job and job.runner.resume())

    def shutdown(self, cancel_current: bool = True) -> None:
        self._stop.set()
        if cancel_current:
            self.cancel_current()
        self._queue.put(None)

    def _work(self) -> None:
        while not self._stop.is_set():
            job = self._queue.get()
            if job is None:
                self._queue.task_done()
                break

            with self._lock:
                self._current = job
            job.status = "running"
            job.started_at = datetime.now().isoformat()

            try:
                state = job.runner.run(
                    job.context,
                    progress_callback=job._progress_callback,
                    resume=job._resume,
                )
                job.status = state.status
                if job._finished_callback:
                    job._finished_callback(job)
            except Exception as exc:
                job.status = "failed"
                job.error = str(exc)
                if job._error_callback:
                    job._error_callback(job, exc)
            finally:
                job.finished_at = datetime.now().isoformat()
                with self._lock:
                    self._current = None
                self._queue.task_done()
