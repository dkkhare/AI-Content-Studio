from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.pipeline import build_project_pipeline
from backend.project.project import Project


class FakeTranslator:
    def translate(self, text, **kwargs):
        return f"translated:{text}"


class FakeRenderer:
    def render(self, context, progress=None):
        output = context.project.output_path() / "fake.mp4"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"video")
        return output


class PipelineFactoryTests(unittest.TestCase):
    def test_default_project_builds_ocr_and_narration(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Project("Demo", Path(temp)).initialize()
            pipeline = build_project_pipeline(project)
            self.assertEqual(
                [stage.stage_id for stage in pipeline.stages],
                ["ocr", "narration"],
            )

    def test_optional_translation_and_video_require_services(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Project("Demo", Path(temp)).initialize()
            project.set_setting("pipeline_translation_enabled", True)
            with self.assertRaises(ValueError):
                build_project_pipeline(project)

            project.set_setting("pipeline_video_enabled", True)
            pipeline = build_project_pipeline(
                project,
                translator=FakeTranslator(),
                renderer=FakeRenderer(),
            )
            self.assertEqual(
                [stage.stage_id for stage in pipeline.stages],
                ["ocr", "translation", "narration", "video"],
            )

    def test_all_stages_can_be_disabled(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Project("Demo", Path(temp)).initialize()
            project.set_setting("pipeline_ocr_enabled", False)
            project.set_setting("pipeline_narration_enabled", False)
            with self.assertRaises(ValueError):
                build_project_pipeline(project)


if __name__ == "__main__":
    unittest.main()
