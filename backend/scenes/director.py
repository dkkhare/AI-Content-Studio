from __future__ import annotations

import json
import re
from hashlib import sha1, sha256
from pathlib import Path
from typing import Any

from backend.episodes import EpisodeReviewStore
from backend.knowledge import KnowledgeReviewStore, KnowledgeStore


class SceneDirectorService:
    """Create reviewable scene plans from approved episodes and approved story knowledge."""

    def __init__(self, project_root: str | Path, ai_manager, *, provider_id: str = "ollama", model: str = ""):
        self.project_root = Path(project_root).resolve()
        self.ai_manager = ai_manager
        self.provider_id = provider_id
        self.model = model
        self.episodes = EpisodeReviewStore(self.project_root)
        self.knowledge = KnowledgeStore(self.project_root)
        self.review = KnowledgeReviewStore(self.project_root)
        self.knowledge.initialize()

    @staticmethod
    def _clean_json_text(text: str) -> str:
        value = str(text or "").strip()
        if value.startswith("```"):
            value = re.sub(r"^```(?:json)?\s*", "", value, flags=re.IGNORECASE)
            value = re.sub(r"\s*```$", "", value)
        first = value.find("{")
        last = value.rfind("}")
        if first >= 0 and last > first:
            value = value[first : last + 1]
        return value

    @classmethod
    def _parse_result(cls, text: str) -> dict[str, Any]:
        try:
            payload = json.loads(cls._clean_json_text(text))
        except json.JSONDecodeError as exc:
            raise ValueError("Scene Director returned invalid JSON.") from exc
        if not isinstance(payload, dict):
            raise ValueError("Scene Director response must be a JSON object.")
        return payload

    def _approved_context(self) -> dict[str, list[dict[str, Any]]]:
        result: dict[str, list[dict[str, Any]]] = {}
        for collection in ("characters", "locations", "objects", "relationships"):
            items = []
            for item in self.knowledge.read(collection):
                if not isinstance(item, dict):
                    continue
                if bool(item.get("approved", False)):
                    items.append(item)
            result[collection] = items
        return result

    def _episode_hash(self, episode_id: str, text: str, context: dict[str, Any]) -> str:
        stable = json.dumps(context, ensure_ascii=False, sort_keys=True)
        return sha256(f"{episode_id}\n{text}\n{stable}".encode("utf-8")).hexdigest()

    def _existing_plan_record(self, episode_id: str) -> dict[str, Any] | None:
        for item in self.knowledge.read("scene_plans"):
            if isinstance(item, dict) and str(item.get("episode_id", "")) == episode_id:
                return item
        return None

    def needs_plan(self, episode_id: str) -> bool:
        episode = self.episodes.get(episode_id)
        text = self.episodes.script(episode_id)
        context = self._approved_context()
        digest = self._episode_hash(episode_id, text, context)
        existing = self._existing_plan_record(episode_id)
        return not existing or str(existing.get("input_sha256", "")) != digest

    def plan_episode(self, episode_id: str, *, force: bool = False) -> dict[str, Any]:
        episode = self.episodes.get(episode_id)
        if not bool(episode.get("approved", False)):
            raise ValueError(f"Episode is not approved for scene planning: {episode_id}")
        if not self.review.review_complete():
            raise ValueError("Story knowledge review must be complete before scene planning.")

        text = self.episodes.script(episode_id).strip()
        if not text:
            raise ValueError(f"Approved episode has no script text: {episode_id}")

        context = self._approved_context()
        digest = self._episode_hash(episode_id, text, context)
        existing = self._existing_plan_record(episode_id)
        if existing and not force and str(existing.get("input_sha256", "")) == digest:
            return dict(existing)

        response = self.ai_manager.execute_prompt(
            "scene_director",
            {
                "episode_id": episode_id,
                "title": str(episode.get("title", episode_id)),
                "text": text,
                "knowledge_json": json.dumps(context, ensure_ascii=False),
            },
            provider_id=self.provider_id,
            model=self.model,
            temperature=0.2,
        )
        payload = self._parse_result(response.text)
        scenes = payload.get("scenes", [])
        if not isinstance(scenes, list) or not scenes:
            raise ValueError("Scene Director did not return any scenes.")

        persisted: list[dict[str, Any]] = []
        for index, raw in enumerate(scenes, start=1):
            if not isinstance(raw, dict):
                continue
            narration = str(raw.get("narration", "")).strip()
            summary = str(raw.get("summary", raw.get("visual_description", ""))).strip()
            if not narration and not summary:
                continue
            scene_id = f"scene_{sha1(f'{episode_id}|{index}|{narration}|{summary}'.encode('utf-8')).hexdigest()[:12]}"
            item = dict(raw)
            item.update(
                {
                    "id": scene_id,
                    "episode_id": episode_id,
                    "sequence": index,
                    "approved": False,
                    "status": "planned",
                }
            )
            self.knowledge.upsert("scenes", item)
            persisted.append(item)

        plan = {
            "id": f"scene_plan_{episode_id}",
            "episode_id": episode_id,
            "input_sha256": digest,
            "scene_ids": [item["id"] for item in persisted],
            "scene_count": len(persisted),
            "approved": False,
            "status": "review_required",
        }
        self.knowledge.upsert("scene_plans", plan)
        return plan

    def plan_approved_episodes(self, *, force: bool = False, progress=None) -> list[dict[str, Any]]:
        approved = self.episodes.approved()
        results: list[dict[str, Any]] = []
        total = len(approved)
        for index, episode in enumerate(approved, start=1):
            episode_id = str(episode.get("episode_id", ""))
            if not episode_id:
                continue
            results.append(self.plan_episode(episode_id, force=force))
            if progress:
                progress(round(index / max(1, total) * 100), f"Planned scenes for episode {index} of {total}")
        return results
