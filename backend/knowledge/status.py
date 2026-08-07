from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .store import KnowledgeStore


class ProjectStatusService:
    """Derive project dashboard state from persisted project assets."""

    def __init__(self, project):
        self.project = project
        self.root = Path(project.root).resolve()
        self.knowledge = KnowledgeStore(self.root)

    def snapshot(self) -> dict[str, Any]:
        self.knowledge.initialize()
        episodes = self._episodes()
        knowledge = self._knowledge_counts()
        approved = sum(1 for item in episodes if bool(item.get("approved", False)))
        skipped = sum(1 for item in episodes if str(item.get("status", "")) == "skipped")
        pending = max(0, len(episodes) - approved - skipped)

        characters = self.knowledge.read("characters")
        locations = self.knowledge.read("locations")
        scenes = self.knowledge.read("scenes")

        return {
            "project_name": self.project.name,
            "language": self.project.language,
            "ocr": self._asset_or_file(self.project.ocr_file, "output/ocr.txt"),
            "spelling": self._file("output/hindi_spelling_corrected.txt"),
            "grammar": self._file("output/hindi_grammar_corrected.txt"),
            "script": self._file("output/podcast_script.txt"),
            "episodes_planned": len(episodes),
            "episodes_approved": approved,
            "episodes_skipped": skipped,
            "episodes_pending": pending,
            "character_count": len(characters) if isinstance(characters, list) else 0,
            "characters_pending": self._pending_approvals(characters),
            "location_count": len(locations) if isinstance(locations, list) else 0,
            "locations_pending": self._pending_approvals(locations),
            "scene_count": len(scenes) if isinstance(scenes, list) else 0,
            "audio_episode_count": self._episode_asset_count("audio", ".wav"),
            "video_episode_count": self._episode_asset_count("video", ".mp4"),
            "knowledge_counts": knowledge,
        }

    def _episodes(self) -> list[dict[str, Any]]:
        manifest = self.root / "segments" / "episodes.json"
        if not manifest.exists():
            return []
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        episodes = data.get("episodes", []) if isinstance(data, dict) else []
        return [item for item in episodes if isinstance(item, dict)]

    def _knowledge_counts(self) -> dict[str, int]:
        try:
            return self.knowledge.counts()
        except (OSError, ValueError, TypeError):
            return {}

    def _asset_or_file(self, configured: str, fallback: str) -> bool:
        if configured:
            path = Path(configured)
            if not path.is_absolute():
                path = self.root / path
            if path.exists():
                return True
        return self._file(fallback)

    def _file(self, relative: str) -> bool:
        return (self.root / relative).exists()

    @staticmethod
    def _pending_approvals(items: Any) -> int:
        if not isinstance(items, list):
            return 0
        return sum(
            1
            for item in items
            if isinstance(item, dict) and not bool(item.get("approved", False))
        )

    def _episode_asset_count(self, folder: str, suffix: str) -> int:
        segments = self.root / "segments"
        if not segments.exists():
            return 0
        count = 0
        for episode in segments.glob("episode_*"):
            target = episode / folder
            if target.exists() and any(path.suffix.lower() == suffix for path in target.rglob(f"*{suffix}")):
                count += 1
        return count
