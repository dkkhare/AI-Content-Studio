from __future__ import annotations

from typing import Any

from backend.knowledge import KnowledgeStore


class SceneReviewStore:
    """Review and edit generated scene plans before any media generation."""

    def __init__(self, project_root):
        self.store = KnowledgeStore(project_root)
        self.store.initialize()

    def scenes(self, episode_id: str | None = None) -> list[dict[str, Any]]:
        items = [dict(item) for item in self.store.read("scenes") if isinstance(item, dict)]
        if episode_id:
            items = [item for item in items if str(item.get("episode_id", "")) == episode_id]
        return sorted(items, key=lambda item: (str(item.get("episode_id", "")), int(item.get("sequence", 0) or 0)))

    def get(self, scene_id: str) -> dict[str, Any]:
        for item in self.scenes():
            if str(item.get("id", "")) == scene_id:
                return item
        raise KeyError(f"Unknown scene: {scene_id}")

    def approve(self, scene_id: str) -> dict[str, Any]:
        item = self.get(scene_id)
        item.update({"approved": True, "status": "approved"})
        saved = self.store.upsert("scenes", item)
        self._sync_plan(str(item.get("episode_id", "")))
        return saved

    def skip(self, scene_id: str) -> dict[str, Any]:
        item = self.get(scene_id)
        item.update({"approved": False, "status": "skipped"})
        saved = self.store.upsert("scenes", item)
        self._sync_plan(str(item.get("episode_id", "")))
        return saved

    def edit(self, scene_id: str, values: dict[str, Any]) -> dict[str, Any]:
        item = self.get(scene_id)
        protected = {"id", "episode_id", "sequence", "approved", "status"}
        for key, value in dict(values).items():
            if key not in protected:
                item[key] = value
        item.update({"approved": False, "status": "edited"})
        saved = self.store.upsert("scenes", item)
        self._sync_plan(str(item.get("episode_id", "")))
        return saved

    def pending(self, episode_id: str | None = None) -> list[dict[str, Any]]:
        return [
            item
            for item in self.scenes(episode_id)
            if not bool(item.get("approved", False))
            and str(item.get("status", "planned")) != "skipped"
        ]

    def approved(self, episode_id: str | None = None) -> list[dict[str, Any]]:
        return [item for item in self.scenes(episode_id) if bool(item.get("approved", False))]

    def review_complete(self, episode_id: str | None = None) -> bool:
        items = self.scenes(episode_id)
        return bool(items) and not self.pending(episode_id)

    def counts(self) -> dict[str, int]:
        items = self.scenes()
        approved = sum(1 for item in items if bool(item.get("approved", False)))
        skipped = sum(1 for item in items if str(item.get("status", "")) == "skipped")
        return {
            "total": len(items),
            "approved": approved,
            "skipped": skipped,
            "pending": max(0, len(items) - approved - skipped),
        }

    def _sync_plan(self, episode_id: str) -> None:
        if not episode_id:
            return
        plans = self.store.read("scene_plans")
        changed = False
        for plan in plans:
            if not isinstance(plan, dict) or str(plan.get("episode_id", "")) != episode_id:
                continue
            complete = self.review_complete(episode_id)
            plan["approved"] = complete
            plan["status"] = "approved" if complete else "review_required"
            changed = True
        if changed:
            self.store.write("scene_plans", plans)
