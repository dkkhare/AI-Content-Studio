from __future__ import annotations

from backend.publishing import PublishingMetadataService

from .stage import PipelineStage


class PublishingMetadataStage(PipelineStage):
    stage_id = "publishing_metadata"
    name = "Publishing and Metadata Studio"
    weight = 1.0

    def execute(self, context, progress=None):
        service = PublishingMetadataService(context.project)
        manifests = service.build_all(progress=progress)
        context.set("publish_manifests", manifests)
        return {"publish_manifests": manifests, "publish_manifest_count": len(manifests)}
