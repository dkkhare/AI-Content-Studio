from __future__ import annotations

from backend.story import StoryIntelligenceService

from .stage import PipelineStage


class StoryIntelligenceStage(PipelineStage):
    stage_id = "story_intelligence"
    name = "Story Intelligence"
    weight = 2.0

    def __init__(self, ai_manager, *, provider_id: str = "ollama", model: str = ""):
        super().__init__()
        self.ai_manager = ai_manager
        self.provider_id = provider_id
        self.model = model

    def execute(self, context, progress=None):
        service = StoryIntelligenceService(
            context.project_root,
            self.ai_manager,
            provider_id=self.provider_id,
            model=self.model,
        )
        results = service.analyze_approved_episodes(progress=progress)
        context.set("story_analyses", results)
        context.set("story_analysis_count", len(results))
        if progress:
            progress(100, f"Story knowledge ready for {len(results)} approved episode(s)")
        return {"story_analyses": results, "story_analysis_count": len(results)}
