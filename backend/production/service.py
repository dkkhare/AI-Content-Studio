from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from backend.episodes import EpisodeReviewStore
from backend.knowledge import KnowledgeStore


def _srt_time(seconds: float) -> str:
    total_ms = max(0, int(round(float(seconds) * 1000.0)))
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


class EpisodeSubtitleService:
    """Build deterministic Hindi SRT subtitles from approved scene narration and durations."""

    def __init__(self, project_root: str | Path, *, words_per_minute: float = 130.0):
        self.root = Path(project_root).resolve()
        self.words_per_minute = max(1.0, float(words_per_minute))
        self.knowledge = KnowledgeStore(self.root)
        self.knowledge.initialize()

    def _scenes(self, episode_id: str) -> list[dict[str, Any]]:
        rows = [
            dict(item)
            for item in self.knowledge.read("scenes")
            if isinstance(item, dict)
            and str(item.get("episode_id", "")) == episode_id
            and bool(item.get("approved", False))
        ]
        return sorted(rows, key=lambda item: int(item.get("sequence", 0) or 0))

    def _duration(self, scene: dict[str, Any], text: str) -> float:
        for key in ("duration_seconds", "estimated_duration_seconds", "duration"):
            try:
                value = float(scene.get(key, 0) or 0)
            except (TypeError, ValueError):
                value = 0.0
            if value > 0:
                return value
        words = max(1, len(text.split()))
        return max(2.0, words / self.words_per_minute * 60.0)

    def generate(self, episode_id: str) -> Path:
        scenes = self._scenes(episode_id)
        if not scenes:
            raise ValueError(f"No approved scenes exist for subtitle generation: {episode_id}")
        blocks: list[str] = []
        cursor = 0.0
        index = 1
        for scene in scenes:
            text = str(scene.get("narration", "")).strip()
            if not text:
                continue
            duration = self._duration(scene, text)
            end = cursor + duration
            blocks.append(f"{index}\n{_srt_time(cursor)} --> {_srt_time(end)}\n{text}")
            cursor = end
            index += 1
        if not blocks:
            raise ValueError(f"Approved scenes contain no narration for subtitles: {episode_id}")
        folder = self.root / "segments" / episode_id / "subtitles"
        folder.mkdir(parents=True, exist_ok=True)
        output = folder / "episode.srt"
        output.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
        self.knowledge.upsert("assets", {
            "id": f"episode_subtitles_{episode_id}",
            "asset_type": "episode_subtitles",
            "owner_id": episode_id,
            "episode_id": episode_id,
            "path": str(output.relative_to(self.root)),
            "approved": True,
            "status": "generated",
        })
        return output


class EpisodeThumbnailService:
    """Prepare a local episode thumbnail from a configured image or first approved scene image."""

    def __init__(self, project_root: str | Path):
        self.root = Path(project_root).resolve()
        self.knowledge = KnowledgeStore(self.root)
        self.knowledge.initialize()

    def _first_scene_image(self, episode_id: str) -> Path | None:
        assets = [
            dict(item)
            for item in self.knowledge.read("assets")
            if isinstance(item, dict)
            and str(item.get("asset_type", "")) == "scene_image"
            and str(item.get("episode_id", "")) == episode_id
            and bool(item.get("approved", False))
        ]
        if not assets:
            return None
        raw = str(assets[0].get("path", "")).strip()
        return (self.root / raw).resolve() if raw else None

    def prepare(self, episode_id: str, configured_path: str = "") -> Path | None:
        source: Path | None = None
        if configured_path:
            candidate = Path(configured_path)
            if not candidate.is_absolute():
                candidate = self.root / candidate
            if candidate.exists() and candidate.is_file():
                source = candidate.resolve()
        if source is None:
            source = self._first_scene_image(episode_id)
        if source is None or not source.exists():
            return None
        folder = self.root / "segments" / episode_id / "export"
        folder.mkdir(parents=True, exist_ok=True)
        suffix = source.suffix.lower() if source.suffix else ".png"
        output = folder / f"thumbnail{suffix}"
        shutil.copyfile(source, output)
        self.knowledge.upsert("assets", {
            "id": f"episode_thumbnail_{episode_id}",
            "asset_type": "episode_thumbnail",
            "owner_id": episode_id,
            "episode_id": episode_id,
            "path": str(output.relative_to(self.root)),
            "source_path": str(source),
            "approved": True,
            "status": "prepared",
        })
        return output


class EpisodeProductionService:
    """Create YouTube-ready episode exports using only local files and FFmpeg."""

    def __init__(self, project, *, runner=None):
        self.project = project
        self.root = Path(project.root).resolve()
        self.ffmpeg_path = str(project.get_setting("ffmpeg_path", "") or "ffmpeg")
        self._runner = runner or subprocess.run
        self.knowledge = KnowledgeStore(self.root)
        self.knowledge.initialize()
        self.episodes = EpisodeReviewStore(self.root)

    def available(self) -> bool:
        path = Path(self.ffmpeg_path)
        return (path.exists() and path.is_file()) or shutil.which(self.ffmpeg_path) is not None

    def _optional_file(self, setting: str) -> Path | None:
        raw = str(self.project.get_setting(setting, "") or "").strip()
        if not raw:
            return None
        path = Path(raw)
        if not path.is_absolute():
            path = self.root / path
        return path.resolve() if path.exists() and path.is_file() else None

    def _base_input(self, episode_id: str) -> tuple[list[str], Path | None]:
        episode = self.root / "segments" / episode_id / "video" / "episode.mp4"
        if not episode.exists():
            raise ValueError(f"Episode video is missing: {episode}")
        intro = self._optional_file("channel_intro_path")
        outro = self._optional_file("channel_outro_path")
        if not intro and not outro:
            return ["-i", str(episode)], None
        concat_file = self.root / "segments" / episode_id / "export" / "production_inputs.txt"
        concat_file.parent.mkdir(parents=True, exist_ok=True)
        paths = [path for path in (intro, episode, outro) if path is not None]
        lines = []
        for path in paths:
            escaped = str(path).replace("'", "'\\''")
            lines.append(f"file '{escaped}'")
        concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return ["-f", "concat", "-safe", "0", "-i", str(concat_file)], concat_file

    def export_episode(self, episode_id: str) -> Path:
        if not self.available():
            raise RuntimeError("FFmpeg was not found. Configure ffmpeg_path or add ffmpeg to PATH.")

        subtitle = None
        if bool(self.project.get_setting("production_subtitles_enabled", True)):
            subtitle = EpisodeSubtitleService(
                self.root,
                words_per_minute=float(self.project.get_setting("hindi_narration_words_per_minute", 130.0)),
            ).generate(episode_id)

        EpisodeThumbnailService(self.root).prepare(
            episode_id,
            str(self.project.get_setting("channel_thumbnail_path", "") or ""),
        )

        base_args, _ = self._base_input(episode_id)
        music = self._optional_file("background_music_path") if bool(self.project.get_setting("background_music_enabled", False)) else None
        watermark = self._optional_file("channel_watermark_path") if bool(self.project.get_setting("channel_watermark_enabled", False)) else None
        output_dir = self.root / "segments" / episode_id / "export"
        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / "youtube.mp4"
        output.unlink(missing_ok=True)

        command = [self.ffmpeg_path, "-y", *base_args]
        music_index = None
        watermark_index = None
        next_index = 1
        if music:
            command.extend(["-stream_loop", "-1", "-i", str(music)])
            music_index = next_index
            next_index += 1
        if watermark:
            command.extend(["-i", str(watermark)])
            watermark_index = next_index

        video_filters: list[str] = []
        if subtitle and bool(self.project.get_setting("production_burn_subtitles", True)):
            escaped = str(subtitle).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
            video_filters.append(f"subtitles='{escaped}'")

        if watermark_index is not None:
            base_label = "0:v"
            if video_filters:
                command.extend(["-filter_complex", f"[{base_label}]{','.join(video_filters)}[vsub];[vsub][{watermark_index}:v]overlay=W-w-24:H-h-24[vout]"])
                command.extend(["-map", "[vout]"])
            else:
                command.extend(["-filter_complex", f"[0:v][{watermark_index}:v]overlay=W-w-24:H-h-24[vout]"])
                command.extend(["-map", "[vout]"])
        elif video_filters:
            command.extend(["-vf", ",".join(video_filters)])

        if music_index is not None:
            volume = float(self.project.get_setting("background_music_volume", 0.12))
            command.extend([
                "-filter_complex" if watermark_index is None else "-filter_complex_script",
            ]) if False else None
            command.extend([
                "-filter_complex",
                f"[0:a][{music_index}:a]amix=inputs=2:duration=first:weights='1 {volume}'[aout]",
                "-map", "[aout]",
            ])
        else:
            command.extend(["-map", "0:a?"])

        command.extend([
            "-c:v", "libx264",
            "-preset", str(self.project.get_setting("production_x264_preset", "medium") or "medium"),
            "-crf", str(int(self.project.get_setting("production_crf", 18))),
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            "-shortest",
            str(output),
        ])

        result = self._runner(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "Unknown FFmpeg error").strip()
            raise RuntimeError(f"Episode production export failed: {detail}")
        if not output.exists():
            raise RuntimeError("FFmpeg completed without creating the final YouTube export.")

        self.knowledge.upsert("assets", {
            "id": f"youtube_export_{episode_id}",
            "asset_type": "youtube_export",
            "owner_id": episode_id,
            "episode_id": episode_id,
            "path": str(output.relative_to(self.root)),
            "approved": True,
            "status": "generated",
        })
        return output

    def export_all(self, *, progress=None) -> list[str]:
        approved = [str(item.get("episode_id", "")) for item in self.episodes.approved() if str(item.get("episode_id", ""))]
        outputs: list[str] = []
        for index, episode_id in enumerate(approved, start=1):
            outputs.append(str(self.export_episode(episode_id)))
            if progress:
                progress(round(index / max(1, len(approved)) * 100), f"Produced episode {index} of {len(approved)}")
        return outputs
