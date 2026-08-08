from __future__ import annotations

from backend.pipeline.stage import PipelineStage


class AITextStage(PipelineStage):
    prompt_name = ""
    output_key = ""
    output_file = ""

    def __init__(self, ai_manager, *, provider_id=None, model=""):
        self.ai_manager = ai_manager
        self.provider_id = provider_id
        self.model = model

    def input_text(self, context) -> str:
        return context.ocr_text

    def variables(self, context, text: str) -> dict:
        return {"text": text}

    def execute(self, context):
        source = self.input_text(context).strip()
        if not source:
            raise ValueError(f"{self.name} requires non-empty input text")
        response = self.ai_manager.execute_prompt(
            self.prompt_name,
            self.variables(context, source),
            provider_id=self.provider_id,
            model=self.model,
        )
        result = response.text.strip()
        if not result:
            raise ValueError(f"{self.name} returned empty output")
        target = context.write_text_atomic(self.output_file, result)
        context.set(self.output_key, result)
        context.set(f"{self.output_key}_file", str(target))
        context.set(f"{self.output_key}_ai", {
            "provider": response.provider,
            "model": response.model,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.total_tokens,
        })
        return result


class AIOCRCleanupStage(AITextStage):
    name = "AI OCR cleanup"
    prompt_name = "ocr_cleanup"
    output_key = "cleaned_text"
    output_file = "output/ocr_cleaned.txt"

    def __init__(self, ai_manager, *, language="English", **kwargs):
        super().__init__(ai_manager, **kwargs)
        self.language = language

    def variables(self, context, text):
        return {"text": text, "language": self.language}

    def execute(self, context):
        result = super().execute(context)
        context.cleaned_text = result
        return result


class HindiSpellingCorrectionStage(AITextStage):
    name = "Hindi spelling correction"
    prompt_name = "hindi_spelling_correction"
    output_key = "spelling_corrected_text"
    output_file = "output/hindi_spelling_corrected.txt"

    def input_text(self, context):
        return context.cleaned_text or context.ocr_text


class HindiGrammarCorrectionStage(AITextStage):
    name = "Hindi grammar correction"
    prompt_name = "hindi_grammar_correction"
    output_key = "grammar_corrected_text"
    output_file = "output/hindi_grammar_corrected.txt"

    def input_text(self, context):
        return context.get("spelling_corrected_text") or context.cleaned_text or context.ocr_text


class AIScriptStage(AITextStage):
    name = "AI script generation"
    prompt_name = "script_generation"
    output_key = "script_text"
    output_file = "output/script.txt"

    def __init__(self, ai_manager, *, language="English", style="natural narration", **kwargs):
        super().__init__(ai_manager, **kwargs)
        self.language = language
        self.style = style

    def input_text(self, context):
        return (
            context.get("grammar_corrected_text")
            or context.get("spelling_corrected_text")
            or context.cleaned_text
            or context.ocr_text
        )

    def variables(self, context, text):
        return {"text": text, "language": self.language, "tone": self.style}
