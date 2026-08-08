from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.ai import AIResponse, AIUsage
from backend.pipeline.ai_stages import (
    AIOCRCleanupStage,
    AIScriptStage,
    HindiGrammarCorrectionStage,
    HindiSpellingCorrectionStage,
)
from backend.pipeline.context import PipelineContext
from backend.project.project import Project


class RecordingManager:
    def __init__(self, text_prefix="result"):
        self.calls = []
        self.text_prefix = text_prefix

    def execute_prompt(self, name, variables=None, **kwargs):
        self.calls.append((name, dict(variables or {}), dict(kwargs)))
        return AIResponse(
            f"{self.text_prefix}:{name}",
            "fake",
            "fake-model",
            AIUsage(3, 2),
        )


class AIPipelineTests(unittest.TestCase):
    def make_context(self, root):
        return PipelineContext(Project("AI test", Path(root)).initialize())

    def test_cleanup_writes_atomic_output_and_metadata(self):
        with tempfile.TemporaryDirectory() as root:
            context = self.make_context(root)
            context.ocr_text = "OCR text"
            stage = AIOCRCleanupStage(RecordingManager(), language="Hindi")
            result = stage.execute(context)
            self.assertEqual(result, "result:ocr_cleanup")
            target = Path(root) / "output" / "ocr_cleaned.txt"
            self.assertEqual(target.read_text(encoding="utf-8"), result)
            self.assertFalse(target.with_suffix(".txt.tmp").exists())
            self.assertEqual(context.get("cleaned_text_ai")["total_tokens"], 5)

    def test_spelling_then_grammar_uses_correct_order(self):
        with tempfile.TemporaryDirectory() as root:
            context = self.make_context(root)
            context.ocr_text = "मूल पाठ"
            manager = RecordingManager()
            HindiSpellingCorrectionStage(manager).execute(context)
            HindiGrammarCorrectionStage(manager).execute(context)
            self.assertEqual(manager.calls[0][0], "hindi_spelling_correction")
            self.assertEqual(manager.calls[1][0], "hindi_grammar_correction")
            self.assertEqual(manager.calls[1][1]["text"], "result:hindi_spelling_correction")

    def test_script_prefers_grammar_corrected_text(self):
        with tempfile.TemporaryDirectory() as root:
            context = self.make_context(root)
            context.ocr_text = "मूल"
            context.set("grammar_corrected_text", "सुधारा गया")
            manager = RecordingManager()
            AIScriptStage(manager, language="Hindi", style="podcast").execute(context)
            _, variables, _ = manager.calls[0]
            self.assertEqual(variables["text"], "सुधारा गया")
            self.assertEqual(variables["language"], "Hindi")
            self.assertEqual(variables["tone"], "podcast")

    def test_empty_input_does_not_overwrite_existing_output(self):
        with tempfile.TemporaryDirectory() as root:
            context = self.make_context(root)
            target = Path(root) / "output" / "hindi_spelling_corrected.txt"
            target.write_text("existing", encoding="utf-8")
            with self.assertRaises(ValueError):
                HindiSpellingCorrectionStage(RecordingManager()).execute(context)
            self.assertEqual(target.read_text(encoding="utf-8"), "existing")


if __name__ == "__main__":
    unittest.main()
