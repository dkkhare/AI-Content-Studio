from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

from .stage import PipelineStage


def _result_text(result: Any) -> str:
    """Normalize provider-specific results into plain text."""
    if result is None:
        return ""
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        for key in ("text", "content", "result"):
            if key in result:
                return str(result[key])
    value = getattr(result, "text", None)
    if value is not None:
        return str(value)
    return str(result)


class OCRStage(PipelineStage):
    """Run the repository OCR manager over one or more project images."""

    stage_id = "ocr"
    name = "OCR"
    weight = 2.0

    def __init__(self, provider: str | None = None, manager_factory: Callable[[], Any] | None = None, image_key: str = "ocr_images"):
        super().__init__()
        self.provider = provider
        self.manager_factory = manager_factory
        self.image_key = image_key

    def _manager(self):
        if self.manager_factory is not None:
            return self.manager_factory()
        from backend.ocr.manager import OCRManager
        return OCRManager()

    def execute(self, context, progress=None):
        images = context.get(self.image_key, [])
        if isinstance(images, (str, Path)):
            images = [images]
        images = [str(Path(item)) for item in images]
        if not images:
            raise ValueError(f"OCR stage requires image paths in context['{self.image_key}'].")

        manager = self._manager()
        if self.provider:
            manager.set_provider(self.provider)

        pages: list[str] = []
        total = len(images)
        for index, image in enumerate(images, start=1):
            result = manager.recognize(image)
            pages.append(_result_text(result))
            if progress:
                progress(round(index / total * 100), f"OCR page {index} of {total}")

        text = "\n\n".join(page for page in pages if page)
        context.set("ocr_pages", pages)
        context.ocr_text = text

        output = context.path("output", "ocr.txt", create_parent=True)
        output.write_text(text, encoding="utf-8")
        context.project.ocr_file = str(output.relative_to(context.project_root))
        return text


class AIPromptStage(PipelineStage):
    """Reusable AI-backed processing stage driven by a named prompt template."""

    stage_id = "ai_prompt"
    name = "AI Prompt"
    weight = 1.5

    def __init__(
        self,
        ai_manager,
        prompt_name: str,
        *,
        source_keys: tuple[str, ...],
        variable_name: str = "text",
        output_key: str,
        output_filename: str,
        provider_id: str | None = None,
        model: str = "",
        extra_variables: dict[str, Any] | None = None,
        project_asset: str | None = None,
        stage_id: str | None = None,
        name: str | None = None,
        weight: float | None = None,
    ):
        super().__init__()
        self.ai_manager = ai_manager
        self.prompt_name = prompt_name
        self.source_keys = tuple(source_keys)
        self.variable_name = variable_name
        self.output_key = output_key
        self.output_filename = output_filename
        self.provider_id = provider_id or None
        self.model = model
        self.extra_variables = dict(extra_variables or {})
        self.project_asset = project_asset
        if stage_id:
            self.stage_id = stage_id
        if name:
            self.name = name
        if weight is not None:
            self.weight = float(weight)

    def _source_text(self, context) -> str:
        for key in self.source_keys:
            if key == "cleaned_text":
                value = context.cleaned_text
            elif key == "ocr_text":
                value = context.ocr_text
            else:
                value = context.get(key)
            if value:
                return str(value)
        return ""

    def execute(self, context, progress=None):
        source = self._source_text(context)
        if not source:
            raise ValueError(f"{self.name} stage has no source text.")

        if progress:
            progress(10, f"Preparing {self.name.lower()}")

        variables = dict(self.extra_variables)
        variables[self.variable_name] = source
        response = self.ai_manager.execute_prompt(
            self.prompt_name,
            variables,
            provider_id=self.provider_id,
            model=self.model,
        )
        text = str(response.text).strip()
        if not text:
            raise ValueError(f"{self.name} returned no text.")

        context.set(self.output_key, text)
        output = context.path("output", self.output_filename, create_parent=True)
        output.write_text(text, encoding="utf-8")

        if self.project_asset:
            try:
                relative = str(output.relative_to(context.project_root))
            except ValueError:
                relative = str(output)
            context.project.register_asset(self.project_asset, relative)

        if progress:
            progress(100, f"{self.name} completed")
        return text


class AIOCRCleanupStage(AIPromptStage):
    stage_id = "ai_ocr_cleanup"
    name = "AI OCR Cleanup"
    weight = 1.5

    def __init__(self, ai_manager, *, provider_id=None, model="", language="en"):
        super().__init__(
            ai_manager,
            "ocr_cleanup",
            source_keys=("ocr_text",),
            variable_name="text",
            output_key="cleaned_text",
            output_filename="ocr_cleaned.txt",
            provider_id=provider_id,
            model=model,
            extra_variables={"language": language},
            stage_id=self.stage_id,
            name=self.name,
            weight=self.weight,
        )

    def execute(self, context, progress=None):
        text = super().execute(context, progress)
        context.cleaned_text = text
        return text


class AITranslationStage(AIPromptStage):
    stage_id = "ai_translation"
    name = "AI Translation"
    weight = 1.5

    def __init__(self, ai_manager, *, provider_id=None, model="", source_language="en", target_language="en"):
        super().__init__(
            ai_manager,
            "translation",
            source_keys=("cleaned_text", "ocr_text"),
            variable_name="source_text",
            output_key="translated_text",
            output_filename="translation_ai.txt",
            provider_id=provider_id,
            model=model,
            extra_variables={
                "source_language": source_language,
                "target_language": target_language,
            },
            project_asset="translation_file",
            stage_id=self.stage_id,
            name=self.name,
            weight=self.weight,
        )

    def execute(self, context, progress=None):
        text = super().execute(context, progress)
        context.cleaned_text = text
        return text


class AISummaryStage(AIPromptStage):
    stage_id = "ai_summary"
    name = "AI Summary"
    weight = 1.0

    def __init__(self, ai_manager, *, provider_id=None, model="", style="concise"):
        super().__init__(
            ai_manager,
            "chapter_summary",
            source_keys=("translated_text", "cleaned_text", "ocr_text"),
            variable_name="text",
            output_key="summary_text",
            output_filename="summary.txt",
            provider_id=provider_id,
            model=model,
            extra_variables={"style": style},
            stage_id=self.stage_id,
            name=self.name,
            weight=self.weight,
        )


class AIScriptStage(AIPromptStage):
    stage_id = "ai_script"
    name = "AI Script Generation"
    weight = 1.5

    def __init__(self, ai_manager, *, provider_id=None, model="", style="natural narration"):
        super().__init__(
            ai_manager,
            "script_generation",
            source_keys=("summary_text", "translated_text", "cleaned_text", "ocr_text"),
            variable_name="text",
            output_key="script_text",
            output_filename="script.txt",
            provider_id=provider_id,
            model=model,
            extra_variables={"style": style},
            stage_id=self.stage_id,
            name=self.name,
            weight=self.weight,
        )


class AISubtitleStage(AIPromptStage):
    stage_id = "ai_subtitles"
    name = "AI Subtitle Generation"
    weight = 1.0

    def __init__(self, ai_manager, *, provider_id=None, model="", language="en"):
        super().__init__(
            ai_manager,
            "subtitle_generation",
            source_keys=("script_text", "translated_text", "cleaned_text", "ocr_text"),
            variable_name="text",
            output_key="subtitle_text",
            output_filename="subtitles.srt",
            provider_id=provider_id,
            model=model,
            extra_variables={"language": language},
            project_asset="subtitle_file",
            stage_id=self.stage_id,
            name=self.name,
            weight=self.weight,
        )


class TranslationStage(PipelineStage):
    """Translate text through an injected translator/provider."""

    stage_id = "translation"
    name = "Translation"
    weight = 1.5

    def __init__(self, translator, source_language: str | None = None, target_language: str | None = None):
        super().__init__()
        self.translator = translator
        self.source_language = source_language
        self.target_language = target_language

    def _translate(self, text: str) -> str:
        function = getattr(self.translator, "translate", self.translator)
        try:
            return str(function(text, source_language=self.source_language, target_language=self.target_language))
        except TypeError:
            return str(function(text))

    def execute(self, context, progress=None):
        pages = list(context.get("ocr_pages", []))
        if not pages:
            source = context.cleaned_text or context.ocr_text
            pages = [source] if source else []
        if not pages:
            raise ValueError("Translation stage has no source text.")

        translated: list[str] = []
        total = len(pages)
        for index, page in enumerate(pages, start=1):
            translated.append(self._translate(str(page)))
            if progress:
                progress(round(index / total * 100), f"Translated page {index} of {total}")

        text = "\n\n".join(translated)
        context.set("translated_pages", translated)
        context.set("translated_text", text)
        context.cleaned_text = text

        output = context.path("output", "translation.txt", create_parent=True)
        output.write_text(text, encoding="utf-8")
        context.project.translation_file = str(output.relative_to(context.project_root))
        return text


class NarrationStage(PipelineStage):
    """Adapt the existing narration/TTS pipeline to ProcessingPipeline."""

    stage_id = "narration"
    name = "Narration / TTS"
    weight = 3.0

    def __init__(self, pipeline_factory: Callable[[], Any] | None = None, output_folder: str = "output/narration"):
        super().__init__()
        self.pipeline_factory = pipeline_factory
        self.output_folder = output_folder

    def _pipeline(self):
        if self.pipeline_factory is not None:
            return self.pipeline_factory()
        from backend.narration.pipeline import NarrationPipeline
        return NarrationPipeline()

    def execute(self, context, progress=None):
        text = (
            context.get("script_text")
            or context.get("translated_text")
            or context.cleaned_text
            or context.ocr_text
        )
        if not text:
            raise ValueError("Narration stage has no source text.")

        if progress:
            progress(5, "Preparing narration")

        output_folder = context.project_root / self.output_folder
        output_folder.mkdir(parents=True, exist_ok=True)
        reference_voice = context.get("reference_voice") or context.project.voice

        job = SimpleNamespace(text=str(text), reference_voice=str(reference_voice or ""), output_folder=str(output_folder))
        output = Path(self._pipeline().generate(job)).resolve()

        context.audio_file = str(output)
        try:
            context.project.narration_file = str(output.relative_to(context.project_root))
        except ValueError:
            context.project.narration_file = str(output)

        if progress:
            progress(100, "Narration generated")
        return str(output)


class VideoRenderStage(PipelineStage):
    """Generic video rendering adapter for the media backend."""

    stage_id = "video"
    name = "Video Render"
    weight = 4.0

    def __init__(self, renderer):
        super().__init__()
        self.renderer = renderer

    def execute(self, context, progress=None):
        function = getattr(self.renderer, "render", self.renderer)
        try:
            output = function(context, progress=progress)
        except TypeError:
            output = function(context)

        if not output:
            raise ValueError("Video renderer did not return an output file.")
        path = Path(output).resolve()
        context.final_video = str(path)
        try:
            context.project.video_file = str(path.relative_to(context.project_root))
        except ValueError:
            context.project.video_file = str(path)
        if progress:
            progress(100, "Video rendered")
        return str(path)
