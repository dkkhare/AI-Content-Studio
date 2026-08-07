from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.knowledge import KnowledgeStore


class VideoAssetReviewStore:
    """Human review state for generated scene clips and assembled episode videos."""

    def __init__(self, project_root: str | Path):
        self.root = Path(project_root).resolve()
        self.knowledge = KnowledgeStore(self.root)
        self.knowledge.initialize()

    def items(self, asset_type: str | None = None) -> list[dict[str, Any]]:
        items = [dict(item) for item in self.knowledge.read("assets") if isinstance(item, dict)]
        if asset_type:
            items = [item for item in items if str(item.get("asset_type", "")) == asset_type]
        return items

    def get(self, asset_id: str) -> dict[str, Any]:
        for item in self.items():
            if str(item.get("id", "")) == asset_id:
                return item
        raise KeyError(f"Unknown video asset: {asset_id}")

    def approve(self, asset_id: str) -> dict[str, Any]:
        item = self.get(asset_id)
        item.update({"approved": True, "status": "approved"})
        return self.knowledge.upsert("assets", item)

    def skip(self, asset_id: str) -> dict[str, Any]:
        item = self.get(asset_id)
        item.update({"approved": False, "status": "skipped"})
        return self.knowledge.upsert("assets", item)

    def request_regeneration(self, asset_id: str) -> dict[str, Any]:
        item = self.get(asset_id)
        item.update({"approved": False, "status": "regenerate_requested"})
        return self.knowledge.upsert("assets", item)

    def pending_clips(self) -> list[dict[str, Any]]:
        return [
            item for item in self.items("scene_video")
            if not bool(item.get("approved", False)) and str(item.get("status", "")) != "skipped"
        ]

    def clip_review_complete(self) -> bool:
        clips = self.items("scene_video")
        return bool(clips) and not self.pending_clips()

    def counts(self) -> dict[str, int]:
        clips = self.items("scene_video")
        approved = sum(1 for item in clips if bool(item.get("approved", False)))
        skipped = sum(1 for item in clips if str(item.get("status", "")) == "skipped")
        return {
            "total": len(clips),
            "approved": approved,
            "skipped": skipped,
            "pending": max(0, len(clips) - approved - skipped),
        }
