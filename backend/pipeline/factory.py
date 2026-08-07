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
            from backend.translation import create_translation_provider

            translator = create_translation_provider(project)

        configured = getattr(translator, "configured", None)
        if callable(configured) and not configured():
            env_name = str(
                project.get_setting("translation_api_key_env", "GOOGLE_TRANSLATE_API_KEY")
            )
            raise ValueError(
                "Translation is enabled but the configured provider has no credentials. "
                f"Set environment variable {env_name}."
            )

        pipeline.add_stage(
            TranslationStage(
                translator=translator,
                source_language=str(
                    project.get_setting("translation_source_language", project.language)
                ),
                target_language=str(
                    project.get_setting("translation_target_language", project.language)
                ),
            )
        )

    if bool(project.get_setting("pipeline_narration_enabled", True)):
        pipeline.add_stage(NarrationStage())

    if bool(project.get_setting("pipeline_video_enabled", False)):
        if renderer is None:
            from backend.video import FFmpegRenderer

            renderer = FFmpegRenderer(
                ffmpeg_path=str(project.get_setting("ffmpeg_path", "")) or None,
                fps=int(project.get_setting("video_fps", 30)),
                seconds_per_image=float(
                    project.get_setting("video_seconds_per_image", 3.0)
                ),
            )
        pipeline.add_stage(VideoRenderStage(renderer))

    if not pipeline.stages:
        raise ValueError("No processing stages are enabled for this project.")

    return pipeline
