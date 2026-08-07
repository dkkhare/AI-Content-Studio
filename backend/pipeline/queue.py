from __future__ import annotations

import json
import queue
import threading
from dataclasses import dataclass, field
from datetime import datetime
from itertools import count
from pathlib import Path
from typing import Callable
from uuid import uuid4

from .runner import PipelineRunner


@dataclass
class PipelineJob:
    context: object
    runner: PipelineRunner
    job_id: str = field(default_factory=lambda: uuid4().hex)
    priority: int = 0
    status: str = "queued"
    progress: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: str = ""
    finished_at: str = ""
    error: str = ""

    @property
    def project_root(self) -> str:
        try:
            return str(self.context.project_root)
        except Exception:
            return ""

    def to_dict(self) -> dict:
        data = {}
        try:
            data = dict(self.context.data)
        except Exception:
            pass
        return {
            "job_id": self.job_id,
            "project_root": self.project_root,
            "priority": self.priority,
            "status": self.status,
            "progress": self.progress,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "error": self.error,
            "data": data,
        }


class PipelineJobQueue:
    """Persistent single-worker priority queue for long-running processing jobs."""

    TERMINAL_STATUSES = {"completed", "failed", "cancelled"}

    def __init__(self, state_file: str | Path | None = None, history_limit: int = 100):
        self._queue: queue.PriorityQueue[tuple[int, int, PipelineJob | None]] = (
            queue.PriorityQueue()
        )
        self._sequence = count()
        self._worker: threading.Thread | None = None
        self._stop = threading.Event()
        self._current: PipelineJob | None = None
        self._lock = threading.RLock()
        self._jobs: dict[str, PipelineJob] = {}
        self.history_limit = max(1, int(history_limit))
        self.state_file = Path(state_file).expanduser() if state_file else None

    @property
    def current(self) -> PipelineJob | None:
        with self._lock:
            return self._current

    @property
    def running(self) -> bool:
        return self._worker is not None and self._worker.is_alive()

    def jobs(self) -> list[PipelineJob]:
        with self._lock:
            return sorted(
                self._jobs.values(),
                key=lambda item: item.created_at,
                reverse=True,
            )

    def records(self) -> list[dict]:
        merged = {
            str(item.get("job_id")): dict(item)
            for item in self.persisted_jobs()
            if item.get("job_id")
        }
        for job in self.jobs():
            merged[job.job_id] = job.to_dict()
        return sorted(
            merged.values(),
            key=lambda item: str(item.get("created_at", "")),
            reverse=True,
        )

    def get(self, job_id: str) -> PipelineJob | None:
        with self._lock:
            return self._jobs.get(job_id)

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
        priority: int = 0,
        progress_callback=None,
        finished_callback: Callable[[PipelineJob], None] | None = None,
        error_callback: Callable[[PipelineJob, Exception], None] | None = None,
        resume: bool = True,
        job_id: str | None = None,
    ) -> PipelineJob:
        job = PipelineJob(
            context=context,
            runner=runner,
            job_id=job_id or uuid4().hex,
            priority=int(priority),
        )
        job._progress_callback = progress_callback
        job._finished_callback = finished_callback
        job._error_callback = error_callback
        job._resume = resume

        with self._lock:
            self._jobs[job.job_id] = job
        self._enqueue(job)
        self._persist()
        self.start()
        return job

    def _enqueue(self, job: PipelineJob) -> None:
        self._queue.put((-job.priority, next(self._sequence), job))

    def cancel_current(self) -> bool:
        job = self.current
        return bool(job and job.runner.cancel())

    def pause_current(self) -> bool:
        job = self.current
        if not job or not job.runner.pause():
            return False
        job.status = "paused"
        self._persist()
        return True

    def resume_current(self) -> bool:
        job = self.current
        if not job or not job.runner.resume():
            return False
        job.status = "running"
        self._persist()
        return True

    def cancel_job(self, job_id: str) -> bool:
        job = self.get(job_id)
        if job is None:
            return False
        if job is self.current:
            return self.cancel_current()
        if job.status != "queued":
            return False
        job.status = "cancelled"
        job.finished_at = datetime.now().isoformat()
        self._persist()
        return True

    def persisted_jobs(self) -> list[dict]:
        if self.state_file is None or not self.state_file.exists():
            return []
        try:
            payload = json.loads(self.state_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        jobs = payload.get("jobs", []) if isinstance(payload, dict) else []
        return [item for item in jobs if isinstance(item, dict)]

    def recover_pending(self, rebuilder) -> list[PipelineJob]:
        """Rebuild queued/interrupted jobs from persisted metadata.

        ``rebuilder(metadata)`` must return ``(context, runner)`` or ``None``.
        Previously-running jobs are treated as interrupted and resumed.
        """
        recovered = []
        for metadata in self.persisted_jobs():
            if metadata.get("status") not in {"queued", "running", "paused", "interrupted"}:
                continue
            rebuilt = rebuilder(metadata)
            if not rebuilt:
                continue
            context, runner = rebuilt
            job = self.submit(
                context,
                runner,
                priority=int(metadata.get("priority", 0)),
                resume=True,
                job_id=str(metadata.get("job_id") or uuid4().hex),
            )
            job.created_at = str(metadata.get("created_at") or job.created_at)
            recovered.append(job)
        self._persist()
        return recovered

    def shutdown(self, cancel_current: bool = True, wait: float | None = None) -> None:
        self._stop.set()
        if cancel_current:
            self.cancel_current()
        self._queue.put((0, next(self._sequence), None))
        worker = self._worker
        if worker and wait is not None:
            worker.join(max(0.0, float(wait)))
        self._persist()

    def _progress(self, job: PipelineJob, callback, progress) -> None:
        job.progress = max(0, min(100, int(getattr(progress, "percent", 0))))
        self._persist()
        if callback:
            try:
                callback(job, progress)
            except TypeError:
                callback(progress)

    def _work(self) -> None:
        while True:
            _, _, job = self._queue.get()
            if job is None:
                self._queue.task_done()
                break

            # A shutdown request can arrive while the worker is blocked in
            # PriorityQueue.get(). Do not start another queued project after
            # that request; leave its persisted status as queued so startup
            # recovery can safely reconstruct it on the next launch.
            if self._stop.is_set():
                self._queue.task_done()
                break

            if job.status == "cancelled":
                self._queue.task_done()
                continue

            with self._lock:
                self._current = job
            job.status = "running"
            job.started_at = datetime.now().isoformat()
            self._persist()

            try:
                callback = getattr(job, "_progress_callback", None)
                state = job.runner.run(
                    job.context,
                    progress_callback=lambda value: self._progress(job, callback, value),
                    resume=getattr(job, "_resume", True),
                )
                job.status = state.status
                if state.status == "completed":
                    job.progress = 100
                finished_callback = getattr(job, "_finished_callback", None)
                if finished_callback:
                    finished_callback(job)
            except Exception as exc:
                job.status = "failed"
                job.error = str(exc)
                error_callback = getattr(job, "_error_callback", None)
                if error_callback:
                    error_callback(job, exc)
            finally:
                job.finished_at = datetime.now().isoformat()
                with self._lock:
                    self._current = None
                self._prune_history()
                self._persist()
                self._queue.task_done()

            if self._stop.is_set():
                break

    def _prune_history(self) -> None:
        with self._lock:
            completed = [
                job
                for job in self._jobs.values()
                if job.status in self.TERMINAL_STATUSES
            ]
            completed.sort(key=lambda item: item.finished_at or item.created_at, reverse=True)
            for job in completed[self.history_limit :]:
                self._jobs.pop(job.job_id, None)

    def _persist(self) -> None:
        if self.state_file is None:
            return
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)

            merged = {
                str(item.get("job_id")): dict(item)
                for item in self.persisted_jobs()
                if item.get("job_id")
                and str(item.get("status", "")) in self.TERMINAL_STATUSES
            }
            for job in self.jobs():
                merged[job.job_id] = job.to_dict()

            records = sorted(
                merged.values(),
                key=lambda item: str(item.get("finished_at") or item.get("created_at", "")),
                reverse=True,
            )
            terminal = [
                item for item in records if str(item.get("status", "")) in self.TERMINAL_STATUSES
            ]
            keep_terminal_ids = {
                str(item.get("job_id")) for item in terminal[: self.history_limit]
            }
            records = [
                item
                for item in records
                if str(item.get("status", "")) not in self.TERMINAL_STATUSES
                or str(item.get("job_id")) in keep_terminal_ids
            ]

            payload = {
                "version": 1,
                "updated_at": datetime.now().isoformat(),
                "jobs": records,
            }
            temp = self.state_file.with_suffix(self.state_file.suffix + ".tmp")
            temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            temp.replace(self.state_file)
        except OSError:
            pass
