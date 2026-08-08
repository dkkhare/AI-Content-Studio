from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.pipeline import FunctionStage, PipelineContext, PipelineStateStore, ProcessingPipeline
from backend.pipeline.state import PipelineState


class DummyProject:
    def __init__(self, root: Path):
        self.root = root


class PipelineReliabilityTests(unittest.TestCase):
    def test_resume_after_restart_restores_checkpoint_data_without_rerunning_completed_stage(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            root.mkdir()
            project = DummyProject(root)
            calls = []
            fail_once = {"value": True}

            def prepare(ctx, progress):
                calls.append("prepare")
                return {"approved_script": "नमस्ते दुनिया", "prepared": True}

            def consume(ctx, progress):
                calls.append("consume")
                self.assertEqual(ctx.get("approved_script"), "नमस्ते दुनिया")
                if fail_once["value"]:
                    fail_once["value"] = False
                    raise RuntimeError("simulated crash")
                return {"consumed": True}

            pipeline = ProcessingPipeline([
                FunctionStage("prepare", "Prepare", prepare),
                FunctionStage("consume", "Consume", consume),
            ])

            with self.assertRaises(Exception):
                pipeline.execute(PipelineContext(project), resume=False)

            failed = PipelineStateStore(root).load()
            self.assertEqual(failed.completed_stage_ids, ["prepare"])
            self.assertEqual(failed.data["approved_script"], "नमस्ते दुनिया")

            # Simulate an application restart: the original context is gone.
            restarted_context = PipelineContext(project)
            completed = pipeline.execute(restarted_context, resume=True)

            self.assertEqual(completed.status, "completed")
            self.assertEqual(calls.count("prepare"), 1)
            self.assertEqual(calls.count("consume"), 2)
            self.assertEqual(restarted_context.get("approved_script"), "नमस्ते दुनिया")
            self.assertTrue(restarted_context.get("consumed"))

    def test_stage_attempts_and_failure_diagnostics_survive_retry(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            root.mkdir()
            project = DummyProject(root)
            fail_once = {"value": True}

            def unstable(ctx, progress):
                if fail_once["value"]:
                    fail_once["value"] = False
                    raise ValueError("temporary model failure")
                return {"ok": True}

            pipeline = ProcessingPipeline([
                FunctionStage("unstable", "Unstable Stage", unstable),
            ])

            with self.assertRaises(Exception):
                pipeline.execute(PipelineContext(project), resume=False)

            failed = PipelineStateStore(root).load()
            self.assertEqual(failed.stage_attempts["unstable"], 1)
            self.assertEqual(len(failed.failures), 1)
            self.assertEqual(failed.failures[0]["stage_id"], "unstable")
            self.assertEqual(failed.failures[0]["error_type"], "ValueError")
            self.assertIn("temporary model failure", failed.failures[0]["message"])

            completed = pipeline.execute(PipelineContext(project), resume=True)
            self.assertEqual(completed.stage_attempts["unstable"], 2)
            self.assertEqual(len(completed.failures), 1)
            self.assertTrue(completed.data["ok"])

    def test_state_store_recovers_from_corrupt_primary_using_backup(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            root.mkdir()
            store = PipelineStateStore(root)

            first = PipelineState(status="failed", completed_stage_ids=["one"], data={"one": True})
            store.save(first)
            second = PipelineState(status="running", completed_stage_ids=["one", "two"], data={"two": True})
            store.save(second)

            self.assertTrue(store.backup_path.is_file())
            store.path.write_text("{ this is not valid json", encoding="utf-8")

            recovered = store.load()
            self.assertEqual(recovered.status, "failed")
            self.assertEqual(recovered.completed_stage_ids, ["one"])
            self.assertTrue(recovered.data["one"])

    def test_explicit_restart_context_values_override_stale_checkpoint_values(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            root.mkdir()
            project = DummyProject(root)
            store = PipelineStateStore(root)
            store.save(PipelineState(
                status="failed",
                completed_stage_ids=["first"],
                data={"input": "old", "derived": "saved"},
            ))

            seen = {}

            def second(ctx, progress):
                seen.update(ctx.data)
                return {}

            pipeline = ProcessingPipeline([
                FunctionStage("first", "First", lambda ctx, progress: {}),
                FunctionStage("second", "Second", second),
            ])
            pipeline.execute(PipelineContext(project, {"input": "new"}), resume=True)

            self.assertEqual(seen["input"], "new")
            self.assertEqual(seen["derived"], "saved")


if __name__ == "__main__":
    unittest.main()
