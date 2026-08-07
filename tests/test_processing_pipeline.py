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


if __name__ == "__main__":
    unittest.main()
