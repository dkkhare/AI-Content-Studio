from __future__ import annotations

from typing import Any

from backend.episodes import EpisodeReviewStore

from .episode_stage import EpisodeNarrationStage, EpisodePlanningStage
from .pipeline import ProcessingPipeline
from .stages import (
    AIOCRCleanupStage,
    AIScriptStage,
    AISubtitleStage,
    AISummaryStage,
    AITranslationStage,
    HindiGrammarCorrectionStage,
    HindiSpellingCorrectionStage,
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
    """Build the Hindi/local-first processing pipeline from project settings."""

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
            "pipeline_hindi_spelling_correction_enabled",
            "pipeline_hindi_grammar_correction_enabled",
            "pipeline_ai_translation_enabled",
            "pipeline_ai_summary_enabled",
            "pipeline_ai_script_enabled",
            "pipeline_ai_subtitle_enabled",
        )
    )
    ai_provider = str(project.get_setting("ai_provider", "ollama") or "ollama")
    ai_model = str(project.get_setting("ai_model", "") or "")

    if ai_enabled and ai_manager is None:
        from backend.ai import AIConfig, AIManager

        ai_manager = AIManager(
            config=AIConfig(
                default_provider=ai_provider,
                default_model=ai_model,
            )
        )

    if bool(project.get_setting("pipeline_ai_ocr_cleanup_enabled", False)):
        pipeline.add_stage(
            AIOCRCleanupStage(
                ai_manager,
                provider_id=ai_provider,
                model=ai_model,
                language=str(project.get_setting("ai_source_language", project.language) or "hi"),
            )
        )

    if bool(project.get_setting("pipeline_hindi_spelling_correction_enabled", False)):
        pipeline.add_stage(
            HindiSpellingCorrectionStage(
                ai_manager,
                provider_id=ai_provider,
                model=ai_model,
            )
        )

    if bool(project.get_setting("pipeline_hindi_grammar_correction_enabled", False)):
        pipeline.add_stage(
            HindiGrammarCorrectionStage(
                ai_manager,
                provider_id=ai_provider,
                model=ai_model,
            )
        )

    if bool(project.get_setting("pipeline_translation_enabled", False)):
        source_language = str(
            project.get_setting("translation_source_language", project.language) or "hi"
        )
        target_language = str(
            project.get_setting("translation_target_language", project.language) or "hi"
        )
        if source_language.lower() != target_language.lower():
            if translator is None:
                from backend.translation import create_translation_provider

                translator = create_translation_provider(project)

            configured = getattr(translator, "configured", None)
            if callable(configured) and not configured():
                env_name = str(
                    project.get_setting(
                        "translation_api_key_env", "GOOGLE_TRANSLATE_API_KEY"
                    )
                )
                raise ValueError(
                    "Translation is enabled but the configured provider has no credentials. "
                    f"Set environment variable {env_name}."
                )

            pipeline.add_stage(
                TranslationStage(
                    translator=translator,
                    source_language=source_language,
                    target_language=target_language,
                )
            )

    if bool(project.get_setting("pipeline_ai_translation_enabled", False)):
        source_language = str(
            project.get_setting("ai_source_language", project.language) or "hi"
        )
        target_language = str(
            project.get_setting("ai_target_language", project.language) or "hi"
        )
        if source_language.lower() != target_language.lower():
            pipeline.add_stage(
                AITranslationStage(
                    ai_manager,
                    provider_id=ai_provider,
                    model=ai_model,
                    source_language=source_language,
                    target_language=target_language,
                )
            )

    if bool(project.get_setting("pipeline_ai_summary_enabled", False)):
        pipeline.add_stage(
            AISummaryStage(
                ai_manager,
                provider_id=ai_provider,
                model=ai_model,
                language=str(project.language or "hi"),
                style=str(project.get_setting("ai_summary_style", "concise") or "concise"),
            )
        )

    if bool(project.get_setting("pipeline_ai_script_enabled", False)):
        pipeline.add_stage(
            AIScriptStage(
                ai_manager,
                provider_id=ai_provider,
                model=ai_model,
                language=str(project.language or "hi"),
                style=str(
                    project.get_setting(
                        "ai_script_style", "natural Hindi podcast narration"
                    )
                    or "natural Hindi podcast narration"
                ),
            )
        )

    segmentation_enabled = bool(
        project.get_setting("pipeline_episode_segmentation_enabled", True)
    )
    review_required = bool(project.get_setting("episode_review_required", True))
    review_store = EpisodeReviewStore(project.root)
    manifest_exists = review_store.exists()
    review_complete = review_store.review_complete() if manifest_exists else False

    media_allowed = True
    if segmentation_enabled:
        if not manifest_exists:
            pipeline.add_stage(
                EpisodePlanningStage(
                    target_minutes=float(project.get_setting("episode_target_minutes", 15.0)),
                    min_minutes=float(project.get_setting("episode_min_minutes", 12.0)),
                    max_minutes=float(project.get_setting("episode_max_minutes", 18.0)),
                    words_per_minute=float(
                        project.get_setting("hindi_narration_words_per_minute", 130.0)
                    ),
                )
            )
            media_allowed = not review_required
        elif review_required:
            media_allowed = review_complete

    if bool(project.get_setting("pipeline_ai_subtitle_enabled", False)) and media_allowed:
        pipeline.add_stage(
            AISubtitleStage(
                ai_manager,
                provider_id=ai_provider,
                model=ai_model,
                language=str(project.get_setting("ai_subtitle_language", "hi") or "hi"),
            )
        )

    if bool(project.get_setting("pipeline_narration_enabled", True)) and media_allowed:
        tts_provider = str(project.get_setting("tts_provider", "f5tts") or "f5tts")
        if tts_provider.lower() != "f5tts":
            raise ValueError(
                f"Unsupported local TTS provider: {tts_provider}. "
                "F5-TTS is the configured local narration engine."
            )
        if segmentation_enabled and review_required:
            pipeline.add_stage(EpisodeNarrationStage())
        else:
            pipeline.add_stage(NarrationStage())

    # Episode-aware video composition will be added after the review gate. Until then,
    # the existing global FFmpeg renderer remains available only when segmentation is off.
    if (
        bool(project.get_setting("pipeline_video_enabled", False))
        and media_allowed
        and not segmentation_enabled
    ):
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
