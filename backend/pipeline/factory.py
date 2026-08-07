from __future__ import annotations

from typing import Any

from .pipeline import ProcessingPipeline
from .stages import NarrationStage, OCRStage, TranslationStage, VideoRenderStage


def build_project_pipeline(
    project,
    *,
    translator: Any | None = None,
    renderer: Any | None = None,
) -> ProcessingPipeline:
    """Build a ProcessingPipeline from project-specific Milestone 12 settings."""

    pipeline = ProcessingPipeline()

    if bool(project.get_setting("pipeline_ocr_enabled", True)):
        pipeline.add_stage(
            OCRStage(
                provider=str(project.get_setting("ocr_provider", "paddle")) or None,
            )
        )

    if bool(project.get_setting("pipeline_translation_enabled", False)):
        if translator is None:
            raise ValueError(
                "Translation is enabled for this project but no translator provider is configured."
            )
        pipeline.add_stage(
            TranslationStage(
                translator=translator,
                source_language=str(project.get_setting("translation_source_language", project.language)),
                target_language=str(project.get_setting("translation_target_language", project.language)),
            )
        )

    if bool(project.get_setting("pipeline_narration_enabled", True)):
        pipeline.add_stage(NarrationStage())

    if bool(project.get_setting("pipeline_video_enabled", False)):
        if renderer is None:
            raise ValueError(
                "Video rendering is enabled for this project but no renderer is configured."
            )
        pipeline.add_stage(VideoRenderStage(renderer))

    if not pipeline.stages:
        raise ValueError("No processing stages are enabled for this project.")

    return pipeline
