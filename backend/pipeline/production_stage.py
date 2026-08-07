from __future__ import annotations

from backend.production import EpisodeProductionService

from .stage import PipelineStage


class EpisodeProductionStage(PipelineStage):
    stage_id = "episode_production"
    name = "Episode Production Studio"
    weight = 3.0

    def execute(self, context, progress=None):
        service = EpisodeProductionService(context.project)
        outputs = service.export_all(progress=progress)
        context.set("youtube_exports", outputs)
        return {"youtube_exports": outputs, "youtube_export_count": len(outputs)}
