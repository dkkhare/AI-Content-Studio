from __future__ import annotations

from backend.episodes import EpisodeReviewStore
from backend.video import (
    EpisodeVideoAssembler,
    SceneVideoService,
    create_local_video_provider,
)

from .stage import PipelineStage


class SceneVideoGenerationStage(PipelineStage):
    stage_id = "scene_videos"
    name = "Local Scene Video Generation"
    weight = 6.0

    def execute(self, context, progress=None):
        provider = create_local_video_provider(context.project)
        service = SceneVideoService(
            context.project_root,
            provider,
            fps=int(context.project.get_setting("video_fps", 24)),
            width=int(context.project.get_setting("video_width", 1920)),
            height=int(context.project.get_setting("video_height", 1080)),
        )
        assets = service.generate_scene_clips(progress=progress)
        context.set("scene_videos", assets)
        return {"scene_videos": assets, "scene_video_count": len(assets)}


class EpisodeVideoAssemblyStage(PipelineStage):
    stage_id = "episode_video_assembly"
    name = "Episode Video Assembly"
    weight = 4.0

    def execute(self, context, progress=None):
        episodes = EpisodeReviewStore(context.project_root).approved()
        episode_ids = [str(item.get("episode_id", "")) for item in episodes if str(item.get("episode_id", ""))]
        assembler = EpisodeVideoAssembler(
            context.project_root,
            ffmpeg_path=str(context.project.get_setting("ffmpeg_path", "") or ""),
        )
        outputs = assembler.assemble_all(episode_ids, progress=progress)
        context.set("episode_videos", outputs)
        return {"episode_videos": outputs, "episode_video_count": len(outputs)}
