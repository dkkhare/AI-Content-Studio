from __future__ import annotations

from pathlib import Path

from .stage import PipelineStage


class _AIStage(PipelineStage):
    prompt_name = ""
    output_key = ""
    output_filename = ""
    weight = 1.0

    def __init__(self, ai_manager, *, provider_id: str = "", model: str = ""):
        super().__init__()
        self.ai_manager = ai_manager
        self.provider_id = str(provider_id or "") or None
        self.model = str(model or "")

    def _source_text(self, context) -> str:
        for key in (
            "script_text",
            "summary_text",
            "translated_text",
            "cleaned_text",
            "ocr_text",
        ):
            value = context.get(key) if hasattr(context, "get") else None
            if not value:
                value = getattr(context, key, None)
            if value:
                return str(value)
        return ""

    def _variables(self, context, text: str) -> dict:
        return {"text": text}

    def _persist(self, context, text: str) -> Path:
        output = context.path("output", self.output_filename, create_parent=True)
        output.write_text(text, encoding="utf-8")
        context.set(self.output_key, text)
        return output

    def execute(self, context, progress=None):
        text = self._source_text(context)
        if not text:
            raise ValueError(f"{self.name} has no source text.")

        if progress:
            progress(10, f"Preparing {self.name}")

        response = self.ai_manager.execute_prompt(
            self.prompt_name,
            self._variables(context, text),
            provider_id=self.provider_id,
            model=self.model,
        )
        result = str(response.text or "").strip()
        if not result:
            raise ValueError(f"{self.name} returned empty text.")

        output = self._persist(context, result)
        if progress:
            progress(100, f"{self.name} completed")
        return {self.output_key: result, f"{self.output_key}_file": str(output)}


class AIOCRCleanupStage(_AIStage):
    stage_id = "ai_ocr_cleanup"
    name = "AI OCR Cleanup"
    prompt_name = "ocr_cleanup"
    output_key = "cleaned_text"
    output_filename = "ocr_cleaned.txt"
    weight = 1.25

    def _source_text(self, context) -> str:
        return str(context.ocr_text or context.get("ocr_text", "") or "")

    def _variables(self, context, text: str) -> dict:
        language = str(getattr(context.project, "language", "hi") or "hi")
        return {"text": text, "language": language}


class AITranslationStage(_AIStage):
    stage_id = "ai_translation"
    name = "AI Translation"
    prompt_name = "translation"
    output_key = "translated_text"
    output_filename = "ai_translation.txt"
    weight = 1.5

    def _variables(self, context, text: str) -> dict:
        project = context.project
        source = str(project.get_setting("ai_source_language", project.language) or "hi")
        target = str(project.get_setting("ai_target_language", project.language) or "hi")
        return {
            "text": text,
            "source_language": source,
            "target_language": target,
        }

    def _persist(self, context, text: str) -> Path:
        output = super()._persist(context, text)
        context.cleaned_text = text
        context.project.translation_file = str(output.relative_to(context.project_root))
        return output


class AISummaryStage(_AIStage):
    stage_id = "ai_summary"
    name = "AI Chapter Summary"
    prompt_name = "chapter_summary"
    output_key = "summary_text"
    output_filename = "summary.txt"
    weight = 1.0

    def _variables(self, context, text: str) -> dict:
        language = str(getattr(context.project, "language", "hi") or "hi")
        style = str(context.project.get_setting("ai_summary_style", "concise") or "concise")
        return {
            "text": text,
            "language": language,
            "audience": f"general readers; style: {style}",
        }


class AIScriptStage(_AIStage):
    stage_id = "ai_script"
    name = "AI Hindi Podcast Script"
    prompt_name = "script_generation"
    output_key = "script_text"
    output_filename = "podcast_script.txt"
    weight = 1.25

    def _variables(self, context, text: str) -> dict:
        language = str(getattr(context.project, "language", "hi") or "hi")
        tone = str(
            context.project.get_setting(
                "ai_script_style", "natural Hindi podcast narration"
            )
            or "natural Hindi podcast narration"
        )
        return {"text": text, "language": language, "tone": tone}


class AISubtitleStage(_AIStage):
    stage_id = "ai_subtitles"
    name = "AI Subtitle Preparation"
    prompt_name = "subtitle_generation"
    output_key = "subtitle_text"
    output_filename = "subtitles.txt"
    weight = 0.75

    def _variables(self, context, text: str) -> dict:
        language = str(
            context.project.get_setting("ai_subtitle_language", "hi") or "hi"
        )
        return {"text": text, "language": language}

    def _persist(self, context, text: str) -> Path:
        output = super()._persist(context, text)
        context.project.subtitle_file = str(output.relative_to(context.project_root))
        return output
