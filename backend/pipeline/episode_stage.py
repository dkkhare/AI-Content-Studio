from __future__ import annotations

from backend.episodes import SegmentPlanner

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

        if progress:
            progress(100, f"Planned {len(episodes)} episode(s) for review")
        return str(manifest)
