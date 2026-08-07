from __future__ import annotations

from backend.scenes import SceneDirectorService

from .stage import PipelineStage


class SceneDirectorStage(PipelineStage):
    stage_id = "scene_director"
    name = "Scene Director"
    weight = 1.5

    def __init__(self, ai_manager, *, provider_id: str = "ollama", model: str = ""):
        super().__init__()
        self.ai_manager = ai_manager
        self.provider_id = provider_id
        self.model = model

    def execute(self, context, progress=None):
        service = SceneDirectorService(
            context.project_root,
            self.ai_manager,
            provider_id=self.provider_id,
            model=self.model,
        )
        plans = service.plan_approved_episodes(progress=progress)
        context.set("scene_plan_count", len(plans))
        if progress:
            progress(100, f"Planned scenes for {len(plans)} approved episode(s); review required")
        return {"scene_plan_count": len(plans)}
