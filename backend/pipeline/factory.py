from __future__ import annotations

from typing import Any

from .pipeline import ProcessingPipeline
from .stages import (
    AIOCRCleanupStage,
    AIScriptStage,
    AISubtitleStage,
    AISummaryStage,
    AITranslationStage,
    NarrationStage,
    OCRStage,
    TranslationStage,
    VideoRenderStage,
)


def build_project_pipeline(
    project,
    *,
    translator: Any | None = None,
    renderer: Any | None = None,
    ai_manager: Any | None = None,
) -> ProcessingPipeline:
    """Build a ProcessingPipeline from project-specific Milestone 12/13 settings."""

    pipeline = ProcessingPipeline()

    if bool(project.get_setting("pipeline_ocr_enabled", True)):
        pipeline.add_stage(
            OCRStage(
                provider=str(project.get_setting("ocr_provider", "paddle")) or None,
            )
        )

    ai_enabled = any(
        bool(project.get_setting(key, False))
        for key in (
            "pipeline_ai_ocr_cleanup_enabled",
            "pipeline_ai_translation_enabled",
            "pipeline_ai_summary_enabled",
            "pipeline_ai_script_enabled",
            "pipeline_ai_subtitle_enabled",
        )
    )
    if ai_enabled and ai_manager is None:
        from backend.ai import AIConfig, AIManager

        ai_manager = AIManager(
            config=AIConfig(
                default_provider=str(project.get_setting("ai_provider", "")),
                default_model=str(project.get_setting("ai_model", "")),
            )
        )

    ai_provider = str(project.get_setting("ai_provider", "")) or None
    ai_model = str(project.get_setting("ai_model", ""))

    if bool(project.get_setting("pipeline_ai_ocr_cleanup_enabled", False)):
        pipeline.add_stage(
            AIOCRCleanupStage(
                ai_manager,
                provider_id=ai_provider,
                model=ai_model,
                language=str(project.get_setting("ai_source_language", project.language)),
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

    if bool(project.get_setting("pipeline_ai_translation_enabled", False)):
        pipeline.add_stage(
            AITranslationStage(
                ai_manager,
                provider_id=ai_provider,
                model=ai_model,
                source_language=str(project.get_setting("ai_source_language", project.language)),
                target_language=str(project.get_setting("ai_target_language", project.language)),
            )
        )

    if bool(project.get_setting("pipeline_ai_summary_enabled", False)):
        pipeline.add_stage(
            AISummaryStage(
                ai_manager,
                provider_id=ai_provider,
                model=ai_model,
                style=str(project.get_setting("ai_summary_style", "concise")),
            )
        )

    if bool(project.get_setting("pipeline_ai_script_enabled", False)):
        pipeline.add_stage(
            AIScriptStage(
                ai_manager,
                provider_id=ai_provider,
                model=ai_model,
                style=str(project.get_setting("ai_script_style", "natural narration")),
            )
        )

    if bool(project.get_setting("pipeline_ai_subtitle_enabled", False)):
        pipeline.add_stage(
            AISubtitleStage(
                ai_manager,
                provider_id=ai_provider,
                model=ai_model,
                language=str(project.get_setting("ai_subtitle_language", project.language)),
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
