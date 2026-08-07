from __future__ import annotations

from backend.images import VisualAssetService, create_image_provider

from .stage import PipelineStage


class ReferenceImageGenerationStage(PipelineStage):
    stage_id = "reference_images"
    name = "Character and Location Reference Images"
    weight = 2.0

    def execute(self, context, progress=None):
        provider = create_image_provider(context.project)
        service = VisualAssetService(context.project_root, provider)
        assets = service.generate_references(progress=progress)
        context.set("reference_images", assets)
        return {"reference_images": assets, "reference_image_count": len(assets)}


class SceneImageGenerationStage(PipelineStage):
    stage_id = "scene_images"
    name = "Scene Image Generation"
    weight = 4.0

    def execute(self, context, progress=None):
        provider = create_image_provider(context.project)
        service = VisualAssetService(context.project_root, provider)
        assets = service.generate_scene_images(progress=progress)
        context.set("scene_images", assets)
        return {"scene_images": assets, "scene_image_count": len(assets)}
