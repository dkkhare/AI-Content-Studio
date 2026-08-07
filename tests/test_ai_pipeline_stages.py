from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.ai import AIResponse
from backend.pipeline.context import PipelineContext
from backend.pipeline.stages import (
    AIOCRCleanupStage,
    AIScriptStage,
    HindiGrammarCorrectionStage,
    HindiSpellingCorrectionStage,
)
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

    def test_spelling_and_grammar_are_separate_and_ordered(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Project("Hindi", Path(temp)).initialize()
            context = PipelineContext(project)
            context.ocr_text = "यह गलत वर्तनी वाला पाठ है"
            manager = RecordingAIManager()

            HindiSpellingCorrectionStage(manager, provider_id="ollama").execute(context)
            self.assertEqual(
                context.get("spelling_corrected_text"),
                "result:hindi_spelling_correction",
            )
            self.assertTrue((Path(temp) / "output" / "hindi_spelling_corrected.txt").exists())

            HindiGrammarCorrectionStage(manager, provider_id="ollama").execute(context)
            self.assertEqual(
                context.get("grammar_corrected_text"),
                "result:hindi_grammar_correction",
            )
            self.assertTrue((Path(temp) / "output" / "hindi_grammar_corrected.txt").exists())

            self.assertEqual(manager.calls[0][0], "hindi_spelling_correction")
            self.assertEqual(manager.calls[0][1]["text"], "यह गलत वर्तनी वाला पाठ है")
            self.assertEqual(manager.calls[1][0], "hindi_grammar_correction")
            self.assertEqual(
                manager.calls[1][1]["text"],
                "result:hindi_spelling_correction",
            )

    def test_grammar_can_run_without_spelling(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Project("Hindi", Path(temp)).initialize()
            context = PipelineContext(project)
            context.ocr_text = "मुझे किताब पढ़ना है"
            manager = RecordingAIManager()

            HindiGrammarCorrectionStage(manager).execute(context)

            self.assertEqual(manager.calls[0][0], "hindi_grammar_correction")
            self.assertEqual(manager.calls[0][1]["text"], "मुझे किताब पढ़ना है")

    def test_podcast_script_prefers_corrected_hindi_text(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Project("Hindi", Path(temp)).initialize()
            context = PipelineContext(project)
            context.ocr_text = "मूल पाठ"
            context.set("grammar_corrected_text", "व्याकरण सुधारा गया पाठ")
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
            self.assertEqual(variables["text"], "व्याकरण सुधारा गया पाठ")
            self.assertEqual(variables["language"], "hi")
            self.assertIn("Hindi podcast", variables["tone"])
            self.assertEqual(context.get("script_text"), "result:script_generation")


if __name__ == "__main__":
    unittest.main()
