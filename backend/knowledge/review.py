from __future__ import annotations

from typing import Any

from .store import KnowledgeStore


class KnowledgeReviewStore:
    """Review/edit/approve/skip/merge story knowledge without silent changes."""

    REVIEWABLE = {"characters", "locations", "objects", "relationships"}

    def __init__(self, project_root):
        self.store = KnowledgeStore(project_root)
        self.store.initialize()

    def items(self, collection: str) -> list[dict[str, Any]]:
        self._check_collection(collection)
        return [dict(item) for item in self.store.read(collection) if isinstance(item, dict)]

    def pending(self, collection: str) -> list[dict[str, Any]]:
        return [
            item for item in self.items(collection)
            if not bool(item.get("approved", False))
            and str(item.get("status", "pending_review")) not in {"skipped", "merged"}
        ]

    def get(self, collection: str, item_id: str) -> dict[str, Any]:
        for item in self.items(collection):
            if str(item.get("id", "")) == item_id:
                return item
        raise KeyError(f"Unknown {collection} item: {item_id}")

    def approve(self, collection: str, item_id: str) -> dict[str, Any]:
        item = self.get(collection, item_id)
        item.update({"approved": True, "status": "approved"})
        return self.store.upsert(collection, item)

    def skip(self, collection: str, item_id: str) -> dict[str, Any]:
        item = self.get(collection, item_id)
        item.update({"approved": False, "status": "skipped"})
        return self.store.upsert(collection, item)

    def edit(self, collection: str, item_id: str, values: dict[str, Any]) -> dict[str, Any]:
        item = self.get(collection, item_id)
        protected = {"id", "approved", "status"}
        for key, value in dict(values).items():
            if key not in protected:
                item[key] = value
        item.update({"approved": False, "status": "edited"})
        return self.store.upsert(collection, item)

    def merge(self, collection: str, source_id: str, target_id: str) -> dict[str, Any]:
        if source_id == target_id:
            raise ValueError("Source and target must be different items.")
        source = self.get(collection, source_id)
        target = self.get(collection, target_id)

        aliases = []
        for value in [target.get("name"), source.get("name"), *target.get("aliases", []), *source.get("aliases", [])]:
            text = str(value or "").strip()
            if text and text not in aliases:
                aliases.append(text)

        episode_ids = []
        for value in [*target.get("episode_ids", []), *source.get("episode_ids", [])]:
            text = str(value or "").strip()
            if text and text not in episode_ids:
                episode_ids.append(text)

        target["aliases"] = [value for value in aliases if value != str(target.get("name", "")).strip()]
        target["episode_ids"] = episode_ids
        target["approved"] = bool(target.get("approved", False))
        target["status"] = "approved" if target["approved"] else "pending_review"
        saved_target = self.store.upsert(collection, target)

        source["approved"] = False
        source["status"] = "merged"
        source["merged_into"] = target_id
        self.store.upsert(collection, source)
        self._resolve_merge_suggestions(source_id, target_id)
        return saved_target

    def review_complete(self) -> bool:
        return all(not self.pending(collection) for collection in self.REVIEWABLE)

    def counts(self) -> dict[str, dict[str, int]]:
        return {
            collection: {
                "total": len(self.items(collection)),
                "pending": len(self.pending(collection)),
            }
            for collection in sorted(self.REVIEWABLE)
        }

    def _resolve_merge_suggestions(self, source_id: str, target_id: str) -> None:
        suggestions = self.store.read("merge_suggestions")
        changed = False
        for item in suggestions:
            if not isinstance(item, dict):
                continue
            pair = {str(item.get("left_id", "")), str(item.get("right_id", ""))}
            if {source_id, target_id} == pair:
                item["status"] = "resolved"
                item["merged_into"] = target_id
                changed = True
        if changed:
            self.store.write("merge_suggestions", suggestions)

    def _check_collection(self, collection: str) -> None:
        if collection not in self.REVIEWABLE:
            raise KeyError(f"Unsupported review collection: {collection}")
