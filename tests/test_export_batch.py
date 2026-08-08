from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from threading import Event
from types import SimpleNamespace

from backend.exporting import (
    BatchExportQueue,
    BatchExportRunner,
    ExportCancelled,
)


class RecordingService:
    def __init__(self, failures=()):
        self.calls = []
        self.failures = set(failures)

    def export(self, project, destination, preset, cancel_event=None):
        self.calls.append((project.root, destination, preset))
        if destination in self.failures:
            self.failures.remove(destination)
            raise OSError("temporary export failure")
        output = Path(destination)
        output.mkdir(parents=True)
        return object(), output.resolve()


def loader(path):
    return SimpleNamespace(root=str(path), name=path.name)


class BatchExportQueueTests(unittest.TestCase):
    def test_unicode_round_trip_and_atomic_save(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "queue.json"
            queue = BatchExportQueue(path)
            job = queue.enqueue(
                Path(root) / "परियोजना",
                Path(root) / "प्रकाशन",
                "publishing",
            )
            loaded = BatchExportQueue.load(path)
            self.assertEqual(loaded.jobs[0].id, job.id)
            self.assertIn("परियोजना", loaded.jobs[0].project_root)
            self.assertFalse(path.with_suffix(".json.tmp").exists())
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["version"], 1)

    def test_duplicate_destination_and_invalid_retry_are_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            queue = BatchExportQueue(Path(root) / "queue.json")
            job = queue.enqueue(Path(root) / "project", Path(root) / "output")
            with self.assertRaisesRegex(ValueError, "already exists"):
                queue.enqueue(Path(root) / "project", Path(root) / "output")
            with self.assertRaisesRegex(ValueError, "failed or cancelled"):
                queue.retry(job.id)

    def test_running_job_recovers_to_pending_after_restart(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "queue.json"
            queue = BatchExportQueue(path)
            job = queue.enqueue(Path(root) / "project", Path(root) / "output")
            queue.replace(job.transition("running", attempts=1))
            recovered = BatchExportQueue.load(path)
            job = recovered.get(job.id)
            self.assertEqual(job.status, "pending")
            self.assertEqual(job.attempts, 1)
            self.assertIn("interrupted shutdown", job.error)
            persisted = BatchExportQueue.load(path, recover=False).get(job.id)
            self.assertEqual(persisted.status, "pending")

    def test_sequential_run_persists_completion_and_never_repeats_it(self):
        with tempfile.TemporaryDirectory() as root:
            queue = BatchExportQueue(Path(root) / "queue.json")
            first = queue.enqueue(Path(root) / "one", Path(root) / "out-one")
            second = queue.enqueue(Path(root) / "two", Path(root) / "out-two", "video")
            service = RecordingService()
            transitions = []
            runner = BatchExportRunner(
                queue, service=service, project_loader=loader
            )
            completed = runner.run_pending(on_job=lambda job: transitions.append(job.status))
            self.assertEqual([job.id for job in completed], [first.id, second.id])
            self.assertEqual([job.status for job in queue.jobs], ["completed", "completed"])
            self.assertEqual([job.attempts for job in queue.jobs], [1, 1])
            self.assertEqual(transitions, ["running", "completed", "running", "completed"])
            runner.run_pending()
            self.assertEqual(len(service.calls), 2)

    def test_failed_job_retry_does_not_duplicate_completed_jobs(self):
        with tempfile.TemporaryDirectory() as root:
            failed_output = str((Path(root) / "failed-output").resolve())
            queue = BatchExportQueue(Path(root) / "queue.json")
            good = queue.enqueue(Path(root) / "good", Path(root) / "good-output")
            bad = queue.enqueue(Path(root) / "bad", failed_output)
            service = RecordingService({failed_output})
            runner = BatchExportRunner(queue, service=service, project_loader=loader)
            runner.run_pending()
            self.assertEqual(queue.get(good.id).status, "completed")
            self.assertEqual(queue.get(bad.id).status, "failed")
            self.assertIn("temporary export failure", queue.get(bad.id).error)

            queue.retry(bad.id)
            runner.run_pending()
            self.assertEqual(queue.get(good.id).attempts, 1)
            self.assertEqual(queue.get(bad.id).status, "completed")
            self.assertEqual(queue.get(bad.id).attempts, 2)
            self.assertEqual(len(service.calls), 3)

    def test_cancellation_stops_queue_and_leaves_later_jobs_pending(self):
        with tempfile.TemporaryDirectory() as root:
            queue = BatchExportQueue(Path(root) / "queue.json")
            first = queue.enqueue(Path(root) / "one", Path(root) / "out-one")
            second = queue.enqueue(Path(root) / "two", Path(root) / "out-two")
            cancelled = Event()

            class CancellingService(RecordingService):
                def export(self, project, destination, preset, cancel_event=None):
                    self.calls.append((project.root, destination, preset))
                    cancel_event.set()
                    raise ExportCancelled("cancelled")

            runner = BatchExportRunner(
                queue, service=CancellingService(), project_loader=loader
            )
            runner.run_pending(cancel_event=cancelled)
            self.assertEqual(queue.get(first.id).status, "cancelled")
            self.assertEqual(queue.get(second.id).status, "pending")
            self.assertEqual(queue.counts()["cancelled"], 1)
            self.assertEqual(queue.counts()["pending"], 1)


if __name__ == "__main__":
    unittest.main()
