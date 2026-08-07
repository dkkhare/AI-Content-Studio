from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.ai import AIResponse
from backend.pipeline import build_project_pipeline
from backend.project.project import Project


class FakeTranslator:
    def configured(self):
        return True

    def translate(self, text, **kwargs):
        return f"translated:{text}"


class FakeRenderer:
    def render(self, context, progress=None):
        output = context.project.output_path() / "fake.mp4"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"video")
        return output


class FakeAIManager:
    def execute_prompt(self, name, variables=None, **kwargs):
        return AIResponse(text=f"{name}:{(variables or {}).get('text', '')}", provider="fake")


class PipelineFactoryTests(unittest.TestCase):
    def test_default_project_builds_hindi_local_first_pipeline(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Project("Demo", Path(temp)).initialize()
            pipeline = build_project_pipeline(project, ai_manager=FakeAIManager())
            self.assertEqual(project.language, "hi")
            self.assertEqual(project.get_setting("ai_provider"), "ollama")
            self.assertEqual(project.get_setting("tts_provider"), "f5tts")
            self.assertFalse(project.get_setting("pipeline_hindi_spelling_correction_enabled"))
            self.assertFalse(project.get_setting("pipeline_hindi_grammar_correction_enabled"))
            self.assertEqual(
                [stage.stage_id for stage in pipeline.stages],
                ["ocr", "ai_script", "narration"],
            )

    def test_spelling_and_grammar_are_independently_optional(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Project("Demo", Path(temp)).initialize()
            project.set_setting("pipeline_hindi_spelling_correction_enabled", True)
            project.set_setting("pipeline_hindi_grammar_correction_enabled", True)
            pipeline = build_project_pipeline(project, ai_manager=FakeAIManager())
            self.assertEqual(
                [stage.stage_id for stage in pipeline.stages],
                [
                    "ocr",
                    "hindi_spelling_correction",
                    "hindi_grammar_correction",
                    "ai_script",
                    "narration",
                ],
            )

            project.set_setting("pipeline_hindi_spelling_correction_enabled", False)
            pipeline = build_project_pipeline(project, ai_manager=FakeAIManager())
            self.assertIn("hindi_grammar_correction", [stage.stage_id for stage in pipeline.stages])
            self.assertNotIn("hindi_spelling_correction", [stage.stage_id for stage in pipeline.stages])

    def test_hindi_to_hindi_translation_is_skipped(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Project("Demo", Path(temp)).initialize()
            project.set_setting("pipeline_translation_enabled", True)
            pipeline = build_project_pipeline(project, ai_manager=FakeAIManager())
            self.assertNotIn("translation", [stage.stage_id for stage in pipeline.stages])

    def test_optional_translation_and_video(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Project("Demo", Path(temp)).initialize()
            project.set_setting("pipeline_translation_enabled", True)
            project.set_setting("translation_target_language", "en")
            project.set_setting("pipeline_video_enabled", True)
            pipeline = build_project_pipeline(
                project,
                translator=FakeTranslator(),
                renderer=FakeRenderer(),
                ai_manager=FakeAIManager(),
            )
            self.assertEqual(
                [stage.stage_id for stage in pipeline.stages],
                ["ocr", "translation", "ai_script", "narration", "video"],
            )

    def test_all_stages_can_be_disabled(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Project("Demo", Path(temp)).initialize()
            project.set_setting("pipeline_ocr_enabled", False)
            project.set_setting("pipeline_ai_ocr_cleanup_enabled", False)
            project.set_setting("pipeline_hindi_spelling_correction_enabled", False)
            project.set_setting("pipeline_hindi_grammar_correction_enabled", False)
            project.set_setting("pipeline_ai_script_enabled", False)
            project.set_setting("pipeline_narration_enabled", False)
            with self.assertRaises(ValueError):
                build_project_pipeline(project, ai_manager=FakeAIManager())


if __name__ == "__main__":
    unittest.main()
