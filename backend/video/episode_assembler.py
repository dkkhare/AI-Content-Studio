from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from backend.knowledge import KnowledgeStore


class EpisodeVideoAssembler:
    """Assemble approved scene clips with episode F5-TTS narration using FFmpeg."""

    def __init__(self, project_root: str | Path, *, ffmpeg_path: str = "", runner=None):
        self.root = Path(project_root).resolve()
        self.ffmpeg_path = str(ffmpeg_path or "ffmpeg")
        self._runner = runner or subprocess.run
        self.knowledge = KnowledgeStore(self.root)
        self.knowledge.initialize()

    def available(self) -> bool:
        path = Path(self.ffmpeg_path)
        return (path.exists() and path.is_file()) or shutil.which(self.ffmpeg_path) is not None

    def _approved_clips(self, episode_id: str):
        clips = [
            dict(item) for item in self.knowledge.read("assets")
            if isinstance(item, dict)
            and str(item.get("asset_type", "")) == "scene_video"
            and str(item.get("episode_id", "")) == episode_id
            and bool(item.get("approved", False))
        ]
        return sorted(clips, key=lambda item: str(item.get("owner_id", "")))

    def assemble_episode(self, episode_id: str) -> Path:
        if not self.available():
            raise RuntimeError("FFmpeg was not found. Configure ffmpeg_path or add ffmpeg to PATH.")
        clips = self._approved_clips(episode_id)
        if not clips:
            raise ValueError(f"No approved scene clips exist for {episode_id}.")
        audio = self.root / "segments" / episode_id / "audio" / "narration.wav"
        if not audio.exists():
            raise ValueError(f"Episode narration is missing: {audio}")

        video_dir = self.root / "segments" / episode_id / "video"
        video_dir.mkdir(parents=True, exist_ok=True)
        concat_file = video_dir / "clips.txt"
        lines = []
        for clip in clips:
            path = (self.root / str(clip.get("path", ""))).resolve()
            escaped = str(path).replace("'", "'\\''")
            lines.append(f"file '{escaped}'")
        concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        output = video_dir / "episode.mp4"
        output.unlink(missing_ok=True)
        command = [
            self.ffmpeg_path,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-i", str(audio),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-shortest",
            str(output),
        ]
        result = self._runner(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "Unknown FFmpeg error").strip()
            raise RuntimeError(f"Episode video assembly failed: {detail}")
        if not output.exists():
            raise RuntimeError("FFmpeg completed without creating the episode video.")

        asset_id = f"episode_video_{episode_id}"
        self.knowledge.upsert(
            "assets",
            {
                "id": asset_id,
                "asset_type": "episode_video",
                "owner_id": episode_id,
                "episode_id": episode_id,
                "path": str(output.relative_to(self.root)),
                "approved": True,
                "status": "generated",
            },
        )
        return output

    def assemble_all(self, episode_ids: list[str], *, progress=None) -> list[str]:
        outputs = []
        for index, episode_id in enumerate(episode_ids, start=1):
            outputs.append(str(self.assemble_episode(episode_id)))
            if progress:
                progress(round(index / max(1, len(episode_ids)) * 100), f"Assembled episode {index} of {len(episode_ids)}")
        return outputs
