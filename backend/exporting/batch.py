from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from threading import Event
from uuid import uuid4

from backend.project.serializer import ProjectSerializer

from .service import ExportCancelled, ProjectExportService


STATUSES = {"pending", "running", "completed", "failed", "cancelled"}
MODES = {"export", "render_export"}
PHASES = {"queued", "render", "export", "done"}


def _now():
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class BatchExportJob:
    project_root: str
    destination: str
    preset: str = "publishing"
    id: str = field(default_factory=lambda: uuid4().hex)
    status: str = "pending"
    attempts: int = 0
    error: str = ""
    output: str = ""
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    mode: str = "export"
    phase: str = "queued"
    render_complete: bool = False
    export_complete: bool = False
    render_output: str = ""

    def __post_init__(self):
        if not self.id.strip():
            raise ValueError("Batch job id is required.")
        if not self.project_root.strip():
            raise ValueError("Batch project root is required.")
        if not self.destination.strip():
            raise ValueError("Batch export destination is required.")
        if not self.preset.strip():
            raise ValueError("Batch export preset is required.")
        if self.status not in STATUSES:
            raise ValueError(f"Invalid batch job status: {self.status}")
        if self.mode not in MODES:
            raise ValueError(f"Invalid batch job mode: {self.mode}")
        if self.phase not in PHASES:
            raise ValueError(f"Invalid batch job phase: {self.phase}")
        if self.attempts < 0:
            raise ValueError("Batch job attempts cannot be negative.")

    def transition(self, status, **changes):
        if status not in STATUSES:
            raise ValueError(f"Invalid batch job status: {status}")
        return replace(self, status=status, updated_at=_now(), **changes)


class BatchExportQueue:
    VERSION = 1

    def __init__(self, path, jobs=()):
        self.path = Path(path)
        self.jobs = list(jobs)
        self._validate()

    def _validate(self):
        ids = [job.id for job in self.jobs]
        if len(ids) != len(set(ids)):
            raise ValueError("Batch queue contains duplicate job ids.")

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(
                {
                    "version": self.VERSION,
                    "jobs": [asdict(job) for job in self.jobs],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.path)
        return self.path

    @classmethod
    def load(cls, path, *, recover=True):
        path = Path(path)
        if not path.is_file():
            return cls(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("version") != cls.VERSION:
            raise ValueError("Unsupported batch queue version.")
        queue = cls(path, [BatchExportJob(**item) for item in data.get("jobs", [])])
        if recover:
            changed = False
            recovered = []
            for job in queue.jobs:
                if job.status == "running":
                    phase = (
                        "export"
                        if job.render_complete or job.mode == "export"
                        else "render"
                    )
                    job = job.transition(
                        "pending",
                        phase=phase,
                        error="Recovered after interrupted shutdown.",
                    )
                    changed = True
                recovered.append(job)
            queue.jobs = recovered
            if changed:
                queue.save()
        return queue

    def enqueue(
        self,
        project_root,
        destination,
        preset="publishing",
        *,
        mode="export",
    ):
        project_root = str(Path(project_root).resolve())
        destination = str(Path(destination).resolve())
        if mode not in MODES:
            raise ValueError(f"Invalid batch job mode: {mode}")
        for job in self.jobs:
            if (
                job.project_root == project_root
                and job.destination == destination
                and job.preset == preset
            ):
                raise ValueError("An export job for this destination already exists.")
        phase = "render" if mode == "render_export" else "export"
        job = BatchExportJob(
            project_root,
            destination,
            preset,
            mode=mode,
            phase=phase,
        )
        self.jobs.append(job)
        self.save()
        return job

    def replace(self, updated):
        for index, job in enumerate(self.jobs):
            if job.id == updated.id:
                self.jobs[index] = updated
                self.save()
                return updated
        raise KeyError(f"Unknown batch job: {updated.id}")

    def retry(self, job_id):
        job = self.get(job_id)
        if job.status not in {"failed", "cancelled"}:
            raise ValueError("Only failed or cancelled jobs can be retried.")
        phase = (
            "export"
            if job.render_complete or job.mode == "export"
            else "render"
        )
        return self.replace(
            job.transition("pending", phase=phase, error="", output="")
        )

    def get(self, job_id):
        for job in self.jobs:
            if job.id == job_id:
                return job
        raise KeyError(f"Unknown batch job: {job_id}")

    def counts(self):
        return {
            status: sum(job.status == status for job in self.jobs)
            for status in sorted(STATUSES)
        }


class BatchExportRunner:
    """Sequential queue runner with independent render/export checkpoints."""

    def __init__(
        self,
        queue,
        *,
        service=None,
        project_loader=None,
        render_project=None,
    ):
        self.queue = queue
        self.service = service or ProjectExportService()
        self.project_loader = project_loader or ProjectSerializer.load
        self.render_project = render_project

    @staticmethod
    def _notify(callback, job):
        if callback is not None:
            callback(job)

    def run_pending(self, *, cancel_event: Event | None = None, on_job=None):
        completed = []
        for snapshot in list(self.queue.jobs):
            job = self.queue.get(snapshot.id)
            if job.status != "pending":
                continue
            if cancel_event is not None and cancel_event.is_set():
                break
            phase = (
                "export"
                if job.render_complete or job.mode == "export"
                else "render"
            )
            job = self.queue.replace(
                job.transition(
                    "running",
                    phase=phase,
                    attempts=job.attempts + 1,
                    error="",
                    output="",
                )
            )
            self._notify(on_job, job)
            try:
                project = self.project_loader(Path(job.project_root))
                if job.mode == "render_export" and not job.render_complete:
                    if self.render_project is None:
                        raise RuntimeError(
                            "Render-then-export job requires a render processor."
                        )
                    render_output = self.render_project(
                        project, job, cancel_event
                    )
                    if cancel_event is not None and cancel_event.is_set():
                        raise ExportCancelled("Batch render was cancelled.")
                    if hasattr(project, "add_output_file"):
                        project.add_output_file("video_file", str(render_output))
                        ProjectSerializer.save(project)
                    else:
                        project.video_file = str(render_output)
                    job = self.queue.replace(
                        job.transition(
                            "running",
                            phase="export",
                            render_complete=True,
                            render_output=str(render_output),
                        )
                    )
                    self._notify(on_job, job)
                _, output = self.service.export(
                    project,
                    job.destination,
                    job.preset,
                    cancel_event=cancel_event,
                )
            except ExportCancelled:
                job = self.queue.replace(
                    self.queue.get(job.id).transition(
                        "cancelled", error="Batch operation cancelled."
                    )
                )
            except Exception as exc:
                job = self.queue.replace(
                    self.queue.get(job.id).transition("failed", error=str(exc))
                )
            else:
                job = self.queue.replace(
                    self.queue.get(job.id).transition(
                        "completed",
                        phase="done",
                        export_complete=True,
                        output=str(output),
                        error="",
                    )
                )
                completed.append(job)
            self._notify(on_job, job)
            if job.status == "cancelled":
                break
        return completed
