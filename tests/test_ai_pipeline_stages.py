from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.ai import AIResponse
from backend.pipeline.context import PipelineContext
from backend.pipeline.stages import AIOCRCleanupStage, AIScriptStage
from backend.project.project import Project


class RecordingAIManager:
    def __init__(self):
        self.calls = []

    def execute_prompt(self, name, variables=None, **kwargs):
        self.calls.append((name, dict(variables or {}), dict(kwargs)))
        return AIResponse(text=f"result:{name}", provider="fake")


class AIPipelineStageTests(unittest.TestCase):
    def test_hindi_ocr_cleanup_passes_text_and_language(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Project("Hindi", Path(temp)).initialize()
            context = PipelineContext(project)
            context.ocr_text = "गलत ओसीआर"
            manager = RecordingAIManager()

            stage = AIOCRCleanupStage(manager, language="hi", provider_id="ollama")
            stage.execute(context)

            name, variables, kwargs = manager.calls[0]
            self.assertEqual(name, "ocr_cleanup")
            self.assertEqual(variables["text"], "गलत ओसीआर")
            self.assertEqual(variables["language"], "hi")
            self.assertEqual(kwargs["provider_id"], "ollama")
            self.assertEqual(context.cleaned_text, "result:ocr_cleanup")

    def test_podcast_script_uses_hindi_language_and_tone(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Project("Hindi", Path(temp)).initialize()
            context = PipelineContext(project)
            context.cleaned_text = "साफ किया गया पाठ"
            manager = RecordingAIManager()

            stage = AIScriptStage(
                manager,
                language="hi",
                style="natural Hindi podcast narration",
                provider_id="ollama",
            )
            stage.execute(context)

            name, variables, _ = manager.calls[0]
            self.assertEqual(name, "script_generation")
            self.assertEqual(variables["text"], "साफ किया गया पाठ")
            self.assertEqual(variables["language"], "hi")
            self.assertIn("Hindi podcast", variables["tone"])
            self.assertEqual(context.get("script_text"), "result:script_generation")


if __name__ == "__main__":
    unittest.main()
