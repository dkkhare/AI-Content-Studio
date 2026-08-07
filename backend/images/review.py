from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.knowledge import KnowledgeStore


class VisualAssetReviewStore:
    """Review state for generated character/location references and scene images."""

    def __init__(self, project_root: str | Path):
        self.root = Path(project_root).resolve()
        self.knowledge = KnowledgeStore(self.root)
        self.knowledge.initialize()

    def items(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self.knowledge.read("assets") if isinstance(item, dict)]

    def pending(self) -> list[dict[str, Any]]:
        return [
            item for item in self.items()
            if str(item.get("asset_type", "")) in {"character_reference", "location_reference", "scene_image"}
            and not bool(item.get("approved", False))
            and str(item.get("status", "pending_review")) != "skipped"
        ]

    def get(self, asset_id: str) -> dict[str, Any]:
        for item in self.items():
            if str(item.get("id", "")) == asset_id:
                return item
        raise KeyError(f"Unknown visual asset: {asset_id}")

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

    def reference_review_complete(self) -> bool:
        references = [
            item for item in self.items()
            if str(item.get("asset_type", "")) in {"character_reference", "location_reference"}
        ]
        return bool(references) and all(
            bool(item.get("approved", False)) or str(item.get("status", "")) == "skipped"
            for item in references
        )

    def scene_review_complete(self) -> bool:
        scenes = [item for item in self.items() if str(item.get("asset_type", "")) == "scene_image"]
        return bool(scenes) and all(
            bool(item.get("approved", False)) or str(item.get("status", "")) == "skipped"
            for item in scenes
        )
