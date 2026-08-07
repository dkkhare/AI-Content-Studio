from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from backend.pipeline import (
    FunctionStage,
    PipelineContext,
    PipelineJobQueue,
    PipelineRunner,
    PipelineStateStore,
    ProcessingPipeline,
)


class DummyProject:
    def __init__(self, root: Path):
        self.root = root


class ProcessingPipelineTests(unittest.TestCase):
    def test_pipeline_persists_progress_and_resumes_failed_stage(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            root.mkdir()
            context = PipelineContext(DummyProject(root))
            calls = []
            fail_once = {"value": True}

            def first(ctx, progress):
                progress(50, "half")
                calls.append("first")
                return {"first": True}

            def second(ctx, progress):
                calls.append("second")
                if fail_once["value"]:
                    fail_once["value"] = False
                    raise RuntimeError("temporary failure")
                progress(100, "done")
                return {"second": True}

            pipeline = ProcessingPipeline([
                FunctionStage("first", "First", first, weight=1),
                FunctionStage("second", "Second", second, weight=2),
            ])
            runner = PipelineRunner(pipeline)

            with self.assertRaises(Exception):
                runner.run(context, resume=False)

            failed = PipelineStateStore(root).load()
            self.assertEqual(failed.status, "failed")
            self.assertEqual(failed.completed_stage_ids, ["first"])

            state = runner.run(context, resume=True)
            self.assertEqual(state.status, "completed")
            self.assertEqual(calls.count("first"), 1)
            self.assertEqual(calls.count("second"), 2)
            self.assertTrue(state.data["first"])
            self.assertTrue(state.data["second"])

    def test_background_runner_can_be_cancelled(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            root.mkdir()
            context = PipelineContext(DummyProject(root))

            def slow(ctx, progress):
                for index in range(100):
                    progress(index, "working")
                    time.sleep(0.005)

            runner = PipelineRunner(
                ProcessingPipeline([FunctionStage("slow", "Slow", slow)])
            )
            runner.start(context, resume=False)
            time.sleep(0.03)
            self.assertTrue(runner.cancel())
            self.assertTrue(runner.wait(2))
            self.assertIsNotNone(runner.last_state)
            self.assertEqual(runner.last_state.status, "cancelled")

    def test_job_queue_executes_submitted_pipeline(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            root.mkdir()
            context = PipelineContext(DummyProject(root))

            def stage(ctx, progress):
                return {"queued": True}

            runner = PipelineRunner(
                ProcessingPipeline([FunctionStage("queued", "Queued", stage)])
            )
            jobs = PipelineJobQueue()
            job = jobs.submit(context, runner, resume=False)

            deadline = time.time() + 2
            while job.status in {"queued", "running"} and time.time() < deadline:
                time.sleep(0.01)

            jobs.shutdown(cancel_current=False)
            self.assertEqual(job.status, "completed")
            self.assertTrue(context.get("queued"))

    def test_job_queue_persists_metadata_and_history(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            root.mkdir()
            state_file = Path(temp) / "queue.json"
            context = PipelineContext(DummyProject(root), {"source": "test"})

            def stage(ctx, progress):
                progress(50, "half")
                return {"persisted": True}

            runner = PipelineRunner(
                ProcessingPipeline([FunctionStage("persist", "Persist", stage)])
            )
            jobs = PipelineJobQueue(state_file=state_file)
            job = jobs.submit(context, runner, priority=7, resume=False)

            deadline = time.time() + 2
            while job.status in {"queued", "running"} and time.time() < deadline:
                time.sleep(0.01)

            jobs.shutdown(cancel_current=False, wait=1)
            records = jobs.persisted_jobs()
            record = next(item for item in records if item["job_id"] == job.job_id)
            self.assertEqual(record["status"], "completed")
            self.assertEqual(record["priority"], 7)
            self.assertEqual(record["progress"], 100)
            self.assertEqual(record["project_root"], str(root.resolve()))
            self.assertTrue(record["data"]["persisted"])

    def test_cancel_queued_job_keeps_history_record(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            root.mkdir()
            state_file = Path(temp) / "queue.json"
            blocker = PipelineContext(DummyProject(root))
            queued = PipelineContext(DummyProject(root))

            def slow(ctx, progress):
                for index in range(20):
                    progress(index * 5, "slow")
                    time.sleep(0.01)

            def fast(ctx, progress):
                return {"should_not_run": True}

            jobs = PipelineJobQueue(state_file=state_file)
            jobs.submit(
                blocker,
                PipelineRunner(ProcessingPipeline([FunctionStage("slow", "Slow", slow)])),
                resume=False,
            )
            job = jobs.submit(
                queued,
                PipelineRunner(ProcessingPipeline([FunctionStage("fast", "Fast", fast)])),
                resume=False,
            )
            self.assertTrue(jobs.cancel_job(job.job_id))

            deadline = time.time() + 2
            while jobs.current is not None and time.time() < deadline:
                time.sleep(0.01)
            jobs.shutdown(cancel_current=False, wait=1)

            self.assertEqual(job.status, "cancelled")
            self.assertFalse(queued.get("should_not_run", False))
            record = next(
                item for item in jobs.persisted_jobs() if item["job_id"] == job.job_id
            )
            self.assertEqual(record["status"], "cancelled")


if __name__ == "__main__":
    unittest.main()
