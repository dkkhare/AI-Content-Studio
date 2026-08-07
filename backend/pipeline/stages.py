from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Iterable

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

    def __init__(
        self,
        provider: str | None = None,
        manager_factory: Callable[[], Any] | None = None,
        image_key: str = "ocr_images",
    ):
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
            raise ValueError(
                f"OCR stage requires image paths in context['{self.image_key}']."
            )

        manager = self._manager()
        if self.provider:
            manager.set_provider(self.provider)

        pages: list[str] = []
        total = len(images)
        for index, image in enumerate(images, start=1):
            result = manager.recognize(image)
            pages.append(_result_text(result))
            if progress:
                progress(
                    round(index / total * 100),
                    f"OCR page {index} of {total}",
                )

        text = "\n\n".join(page for page in pages if page)
        context.set("ocr_pages", pages)
        context.ocr_text = text

        output = context.path("output", "ocr.txt", create_parent=True)
        output.write_text(text, encoding="utf-8")
        context.project.ocr_file = str(output.relative_to(context.project_root))
        return text


class TranslationStage(PipelineStage):
    """Translate text through an injected translator/provider.

    The translator may be a callable or an object exposing ``translate``.
    This keeps the pipeline independent of a particular cloud/model provider.
    """

    stage_id = "translation"
    name = "Translation"
    weight = 1.5

    def __init__(
        self,
        translator,
        source_language: str | None = None,
        target_language: str | None = None,
    ):
        super().__init__()
        self.translator = translator
        self.source_language = source_language
        self.target_language = target_language

    def _translate(self, text: str) -> str:
        function = getattr(self.translator, "translate", self.translator)
        try:
            return str(
                function(
                    text,
                    source_language=self.source_language,
                    target_language=self.target_language,
                )
            )
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
                progress(
                    round(index / total * 100),
                    f"Translated page {index} of {total}",
                )

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

    def __init__(
        self,
        pipeline_factory: Callable[[], Any] | None = None,
        output_folder: str = "output/narration",
    ):
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
            context.get("translated_text")
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

        job = SimpleNamespace(
            text=str(text),
            reference_voice=str(reference_voice or ""),
            output_folder=str(output_folder),
        )
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
    """Generic video rendering adapter for the future media backend.

    ``renderer`` may be a callable or an object exposing ``render``. The
    renderer receives the pipeline context and may optionally accept a progress
    callback. Keeping rendering injected avoids coupling the core to a video
    engine that the repository does not yet provide.
    """

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
