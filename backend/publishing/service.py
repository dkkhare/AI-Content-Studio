from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from backend.episodes import EpisodeReviewStore
from backend.knowledge import KnowledgeStore


class PublishingMetadataService:
    """Build deterministic Hindi YouTube/podcast metadata from approved project data."""

    def __init__(self, project):
        self.project = project
        self.root = Path(project.root).resolve()
        self.episodes = EpisodeReviewStore(self.root)
        self.knowledge = KnowledgeStore(self.root)
        self.knowledge.initialize()

    @staticmethod
    def _timestamp(seconds: float) -> str:
        value = max(0, int(round(float(seconds or 0))))
        hours, remainder = divmod(value, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"

    @staticmethod
    def _clean_text(value: str) -> str:
        return re.sub(r"\s+", " ", str(value or "")).strip()

    def _asset_path(self, episode_id: str, asset_type: str) -> str:
        for item in self.knowledge.read("assets"):
            if not isinstance(item, dict):
                continue
            if str(item.get("episode_id", item.get("owner_id", ""))) != episode_id:
                continue
            if str(item.get("asset_type", "")) == asset_type:
                return str(item.get("path", ""))
        return ""

    def _chapters(self, episode_id: str) -> list[dict[str, Any]]:
        scenes = [
            dict(item) for item in self.knowledge.read("scenes")
            if isinstance(item, dict)
            and str(item.get("episode_id", "")) == episode_id
            and bool(item.get("approved", False))
        ]
        scenes.sort(key=lambda item: int(item.get("sequence", 0) or 0))
        elapsed = 0.0
        chapters = []
        for index, scene in enumerate(scenes, start=1):
            title = self._clean_text(
                scene.get("chapter_title")
                or scene.get("summary")
                or scene.get("visual_description")
                or f"दृश्य {index}"
            )
            chapters.append({
                "index": index,
                "timestamp": self._timestamp(elapsed),
                "seconds": round(elapsed, 2),
                "title": title[:100],
                "scene_id": str(scene.get("id", "")),
            })
            elapsed += float(scene.get("duration_seconds", scene.get("estimated_duration_seconds", 0)) or 0)
        return chapters

    def _keywords(self, episode_id: str) -> list[str]:
        values: list[str] = []
        configured = str(self.project.get_setting("publishing_default_keywords", "") or "")
        values.extend(part.strip() for part in configured.split(",") if part.strip())
        for collection in ("characters", "locations", "objects"):
            for item in self.knowledge.read(collection):
                if not isinstance(item, dict) or not bool(item.get("approved", False)):
                    continue
                appearances = [str(v) for v in item.get("episode_ids", item.get("episodes", [])) if str(v)]
                if appearances and episode_id not in appearances:
                    continue
                name = self._clean_text(item.get("name", ""))
                if name:
                    values.append(name)
        values.extend(["हिंदी ऑडियोबुक", "हिंदी पॉडकास्ट", "Hindi Audiobook"])
        result = []
        seen = set()
        for value in values:
            key = value.casefold()
            if key not in seen:
                seen.add(key)
                result.append(value)
        return result[:25]

    def build_episode(self, episode_id: str) -> dict[str, Any]:
        episode = self.episodes.get(episode_id)
        if not bool(episode.get("approved", False)):
            raise ValueError(f"Episode is not approved for publishing metadata: {episode_id}")
        script = self._clean_text(self.episodes.script(episode_id))
        base_title = self._clean_text(episode.get("title", "")) or episode_id.replace("_", " ").title()
        prefix = self._clean_text(self.project.get_setting("publishing_title_prefix", ""))
        suffix = self._clean_text(self.project.get_setting("publishing_title_suffix", ""))
        title = " ".join(part for part in (prefix, base_title, suffix) if part).strip()[:100]
        chapters = self._chapters(episode_id)
        chapter_text = "\n".join(f"{item['timestamp']} {item['title']}" for item in chapters)
        channel_name = self._clean_text(self.project.get_setting("publishing_channel_name", ""))
        description_intro = self._clean_text(self.project.get_setting("publishing_description_intro", ""))
        excerpt = script[:900].rstrip()
        description_parts = [part for part in (description_intro, excerpt) if part]
        if chapter_text:
            description_parts.append("अध्याय / Chapters:\n" + chapter_text)
        if channel_name:
            description_parts.append(f"चैनल: {channel_name}")
        description = "\n\n".join(description_parts)
        keywords = self._keywords(episode_id)

        video = self._asset_path(episode_id, "youtube_export") or f"segments/{episode_id}/export/youtube.mp4"
        thumbnail = self._asset_path(episode_id, "episode_thumbnail") or f"segments/{episode_id}/export/thumbnail.png"
        subtitles = self._asset_path(episode_id, "episode_subtitles") or f"segments/{episode_id}/subtitles/episode.srt"
        narration = f"segments/{episode_id}/audio/narration.wav"
        episode_number = int(episode.get("episode_number", episode.get("sequence", 0)) or 0)

        manifest = {
            "schema_version": 1,
            "episode_id": episode_id,
            "language": "hi",
            "youtube": {
                "title": title,
                "description": description,
                "tags": keywords,
                "chapters": chapters,
                "category": str(self.project.get_setting("publishing_youtube_category", "Education") or "Education"),
                "privacy": str(self.project.get_setting("publishing_youtube_privacy", "private") or "private"),
                "thumbnail_text": self._clean_text(self.project.get_setting("publishing_thumbnail_text", "")) or base_title,
            },
            "podcast": {
                "title": title,
                "description": description,
                "episode_number": episode_number,
                "explicit": bool(self.project.get_setting("publishing_podcast_explicit", False)),
                "author": self._clean_text(self.project.author),
                "show": channel_name or self._clean_text(self.project.name),
                "language": "hi-IN",
            },
            "files": {
                "video": video,
                "thumbnail": thumbnail,
                "subtitles": subtitles,
                "audio": narration,
            },
            "ready": bool((self.root / video).exists()),
        }
        output_dir = self.root / "segments" / episode_id / "publish"
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / "manifest.json"
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        self.knowledge.upsert("assets", {
            "id": f"publish_manifest_{episode_id}",
            "asset_type": "publish_manifest",
            "owner_id": episode_id,
            "episode_id": episode_id,
            "path": str(path.relative_to(self.root)),
            "approved": True,
            "status": "generated",
        })
        return manifest

    def build_all(self, *, progress=None) -> list[dict[str, Any]]:
        approved = self.episodes.approved()
        outputs = []
        for index, item in enumerate(approved, start=1):
            episode_id = str(item.get("episode_id", ""))
            if not episode_id:
                continue
            outputs.append(self.build_episode(episode_id))
            if progress:
                progress(round(index / max(1, len(approved)) * 100), f"Prepared publishing metadata {index} of {len(approved)}")
        return outputs
