from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

from backend.episodes import EpisodeReviewStore, SegmentPlanner

from .stage import PipelineStage


class EpisodePlanningStage(PipelineStage):
    stage_id = "episode_planning"
    name = "Episode Planning"
    weight = 1.0

    def __init__(
        self,
        *,
        target_minutes: float = 15.0,
        min_minutes: float = 12.0,
        max_minutes: float = 18.0,
        words_per_minute: float = 130.0,
    ):
        super().__init__()
        self.planner = SegmentPlanner(
            target_minutes=target_minutes,
            min_minutes=min_minutes,
            max_minutes=max_minutes,
            words_per_minute=words_per_minute,
        )

    @staticmethod
    def _source_text(context) -> str:
        for key in (
            "script_text",
            "translated_text",
            "grammar_corrected_text",
            "spelling_corrected_text",
        ):
            value = context.get(key)
            if value:
                return str(value)
        return str(context.cleaned_text or context.ocr_text or "")

    def execute(self, context, progress=None):
        text = self._source_text(context)
        if not text:
            raise ValueError("Episode planning stage has no source text.")

        if progress:
            progress(10, "Planning logical ~15 minute episodes")

        episodes = self.planner.plan(text)
        if not episodes:
            raise ValueError("Episode planner could not create any episodes.")

        manifest = self.planner.persist(context.project_root, episodes)
        context.set("episodes", [episode.to_dict() for episode in episodes])
        context.set("episode_manifest", str(manifest))
        context.set("episode_review_required", True)

        if progress:
            progress(100, f"Planned {len(episodes)} episode(s) for review")
        return str(manifest)


class EpisodeNarrationStage(PipelineStage):
    """Generate F5-TTS audio only for explicitly approved episodes."""

    stage_id = "episode_narration"
    name = "Approved Episode F5-TTS"
    weight = 3.0

    def __init__(self, pipeline_factory: Callable[[], Any] | None = None):
        super().__init__()
        self.pipeline_factory = pipeline_factory

    def _pipeline(self):
        if self.pipeline_factory is not None:
            return self.pipeline_factory()
        from backend.narration.pipeline import NarrationPipeline

        return NarrationPipeline()

    def execute(self, context, progress=None):
        store = EpisodeReviewStore(context.project_root)
        if not store.exists():
            raise ValueError("Episode manifest is missing. Plan episodes before narration.")
        if not store.review_complete():
            raise ValueError("Episode review is incomplete. Approve or skip every episode first.")

        approved = store.approved()
        if not approved:
            raise ValueError("No episodes are approved for narration.")

        reference_voice = context.get("reference_voice") or context.project.voice
        if not reference_voice:
            raise ValueError("F5-TTS narration requires a local reference voice audio file.")

        outputs: list[dict[str, str]] = []
        total = len(approved)
        for index, episode in enumerate(approved, start=1):
            episode_id = str(episode.get("episode_id"))
            text = store.script(episode_id).strip()
            if not text:
                raise ValueError(f"Approved episode {episode_id} has an empty script.")

            output_folder = context.project_root / "segments" / episode_id / "audio"
            output_folder.mkdir(parents=True, exist_ok=True)
            if progress:
                progress(
                    int(((index - 1) / total) * 100),
                    f"Generating Hindi narration for {episode_id} ({index}/{total})",
                )

            job = SimpleNamespace(
                text=text,
                reference_voice=str(reference_voice),
                output_folder=str(output_folder),
            )
            output = Path(self._pipeline().generate(job)).resolve()
            outputs.append({"episode_id": episode_id, "audio_file": str(output)})

        context.set("episode_audio_files", outputs)
        context.audio_file = outputs[-1]["audio_file"]
        first_output = Path(outputs[0]["audio_file"])
        try:
            relative = str(first_output.relative_to(context.project_root))
        except ValueError:
            relative = str(first_output)
        context.project.narration_file = relative
        context.project.podcast_file = relative

        if progress:
            progress(100, f"Generated F5-TTS narration for {len(outputs)} approved episode(s)")
        return outputs
