from __future__ import annotations

from datetime import datetime
from difflib import SequenceMatcher
from hashlib import sha1, sha256
import json
import re
from pathlib import Path
from typing import Any

from backend.episodes import EpisodeReviewStore
from backend.knowledge import KnowledgeStore


_HONORIFICS = (
    "श्री",
    "श्रीमती",
    "कुमारी",
    "डॉ",
    "डॉ.",
    "पंडित",
    "महात्मा",
    "भगवान",
    "स्वामी",
    "गुरु",
)


class StoryIntelligenceService:
    """Analyze approved Hindi episodes and persist reusable story knowledge."""

    def __init__(
        self,
        project_root: str | Path,
        ai_manager,
        *,
        provider_id: str = "ollama",
        model: str = "",
    ):
        self.project_root = Path(project_root).resolve()
        self.ai_manager = ai_manager
        self.provider_id = provider_id
        self.model = model
        self.episodes = EpisodeReviewStore(self.project_root)
        self.knowledge = KnowledgeStore(self.project_root)
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
            raise ValueError("Story Intelligence returned invalid JSON.") from exc
        if not isinstance(payload, dict):
            raise ValueError("Story Intelligence response must be a JSON object.")
        return payload

    @staticmethod
    def _normalized_name(value: str) -> str:
        return re.sub(r"[^\w\u0900-\u097f]+", "", str(value or "").casefold())

    @classmethod
    def _comparison_name(cls, value: str) -> str:
        text = str(value or "").strip()
        for prefix in _HONORIFICS:
            if text.casefold().startswith(prefix.casefold()):
                text = text[len(prefix) :].strip(" .:-—")
                break
        return cls._normalized_name(text)

    @classmethod
    def _stable_id(cls, kind: str, name: str, episode_id: str = "") -> str:
        source = f"{kind}|{cls._normalized_name(name)}|{episode_id if kind in {'event', 'scene'} else ''}"
        digest = sha1(source.encode("utf-8")).hexdigest()[:12]
        return f"{kind}_{digest}"

    @staticmethod
    def _as_list(value: Any) -> list:
        return value if isinstance(value, list) else []

    @staticmethod
    def _as_dict(value: Any) -> dict:
        return value if isinstance(value, dict) else {}

    def _analysis_record(self, episode_id: str) -> dict | None:
        for item in self.knowledge.read("analyses"):
            if isinstance(item, dict) and str(item.get("episode_id", "")) == episode_id:
                return item
        return None

    def _script_hash(self, text: str) -> str:
        return sha256(text.encode("utf-8")).hexdigest()

    def needs_analysis(self, episode_id: str) -> bool:
        text = self.episodes.script(episode_id)
        existing = self._analysis_record(episode_id)
        return not existing or str(existing.get("script_sha256", "")) != self._script_hash(text)

    def _entity_id(self, collection: str, kind: str, name: str) -> str:
        normalized = self._normalized_name(name)
        for existing in self.knowledge.read(collection):
            if not isinstance(existing, dict):
                continue
            if self._normalized_name(existing.get("name", "")) == normalized:
                return str(existing.get("id"))
        return self._stable_id(kind, name)

    def _merge_suggestions(self, collection: str, kind: str, entity: dict) -> None:
        name = str(entity.get("name", "")).strip()
        if not name:
            return
        incoming_core = self._comparison_name(name)
        incoming_aliases = {
            self._normalized_name(alias)
            for alias in self._as_list(entity.get("aliases"))
            if str(alias).strip()
        }
        for existing in self.knowledge.read(collection):
            if not isinstance(existing, dict) or existing.get("id") == entity.get("id"):
                continue
            existing_name = str(existing.get("name", "")).strip()
            existing_core = self._comparison_name(existing_name)
            existing_aliases = {
                self._normalized_name(alias)
                for alias in self._as_list(existing.get("aliases"))
                if str(alias).strip()
            }
            ratio = SequenceMatcher(None, incoming_core, existing_core).ratio() if incoming_core and existing_core else 0.0
            alias_overlap = bool(incoming_aliases & ({self._normalized_name(existing_name)} | existing_aliases))
            same_core = bool(incoming_core and incoming_core == existing_core)
            if not (same_core or alias_overlap or ratio >= 0.88):
                continue
            pair = sorted([str(entity.get("id")), str(existing.get("id"))])
            suggestion_id = f"merge_{sha1(('|'.join(pair)).encode('utf-8')).hexdigest()[:12]}"
            self.knowledge.upsert(
                "merge_suggestions",
                {
                    "id": suggestion_id,
                    "entity_type": kind,
                    "left_id": pair[0],
                    "right_id": pair[1],
                    "reason": "same_core" if same_core else "alias_overlap" if alias_overlap else "similar_name",
                    "status": "pending",
                },
            )

    def _persist_named_entities(self, collection: str, kind: str, values: list, episode_id: str) -> int:
        count = 0
        for raw in values:
            item = self._as_dict(raw)
            name = str(item.get("name", "")).strip()
            if not name:
                continue
            entity_id = self._entity_id(collection, kind, name)
            existing = next(
                (
                    row
                    for row in self.knowledge.read(collection)
                    if isinstance(row, dict) and str(row.get("id", "")) == entity_id
                ),
                {},
            )
            appearances = list(existing.get("episode_ids", [])) if isinstance(existing, dict) else []
            if episode_id not in appearances:
                appearances.append(episode_id)
            aliases = list(dict.fromkeys(
                [str(value).strip() for value in self._as_list(existing.get("aliases")) + self._as_list(item.get("aliases")) if str(value).strip()]
            ))
            persisted = dict(existing)
            persisted.update(item)
            persisted.update(
                {
                    "id": entity_id,
                    "name": name,
                    "aliases": aliases,
                    "episode_ids": appearances,
                    "approved": bool(existing.get("approved", False)),
                    "status": str(existing.get("status", "pending_review")),
                }
            )
            saved = self.knowledge.upsert(collection, persisted)
            self._merge_suggestions(collection, kind, saved)
            count += 1
        return count

    def _persist_relationships(self, values: list, episode_id: str) -> int:
        count = 0
        characters = self.knowledge.read("characters")
        name_to_id = {
            self._normalized_name(item.get("name", "")): str(item.get("id"))
            for item in characters
            if isinstance(item, dict)
        }
        for raw in values:
            item = self._as_dict(raw)
            source = str(item.get("source", "")).strip()
            target = str(item.get("target", "")).strip()
            relation = str(item.get("relationship", item.get("type", ""))).strip()
            if not source or not target or not relation:
                continue
            source_id = name_to_id.get(self._normalized_name(source), self._stable_id("character", source))
            target_id = name_to_id.get(self._normalized_name(target), self._stable_id("character", target))
            relation_id = "relationship_" + sha1(
                f"{source_id}|{relation.casefold()}|{target_id}".encode("utf-8")
            ).hexdigest()[:12]
            existing = next(
                (
                    row
                    for row in self.knowledge.read("relationships")
                    if isinstance(row, dict) and str(row.get("id", "")) == relation_id
                ),
                {},
            )
            episode_ids = list(existing.get("episode_ids", [])) if isinstance(existing, dict) else []
            if episode_id not in episode_ids:
                episode_ids.append(episode_id)
            persisted = dict(item)
            persisted.update(
                {
                    "id": relation_id,
                    "source": source,
                    "source_id": source_id,
                    "target": target,
                    "target_id": target_id,
                    "relationship": relation,
                    "episode_ids": episode_ids,
                    "approved": bool(existing.get("approved", False)),
                    "status": str(existing.get("status", "pending_review")),
                }
            )
            self.knowledge.upsert("relationships", persisted)
            count += 1
        return count

    def _persist_events(self, values: list, episode_id: str) -> int:
        count = 0
        for index, raw in enumerate(values, start=1):
            item = self._as_dict(raw)
            summary = str(item.get("summary", item.get("event", ""))).strip()
            if not summary:
                continue
            event_id = self._stable_id("event", f"{index}:{summary}", episode_id)
            persisted = dict(item)
            persisted.update(
                {
                    "id": event_id,
                    "episode_id": episode_id,
                    "summary": summary,
                    "sequence": index,
                }
            )
            self.knowledge.upsert("events", persisted)
            self.knowledge.upsert("timeline", persisted)
            count += 1
        return count

    def _persist_scenes(self, values: list, episode_id: str) -> int:
        count = 0
        for index, raw in enumerate(values, start=1):
            item = self._as_dict(raw)
            summary = str(item.get("summary", item.get("description", ""))).strip()
            if not summary:
                continue
            scene_id = self._stable_id("scene", f"{index}:{summary}", episode_id)
            persisted = dict(item)
            persisted.update(
                {
                    "id": scene_id,
                    "episode_id": episode_id,
                    "sequence": index,
                    "summary": summary,
                    "approved": False,
                    "status": "candidate",
                }
            )
            self.knowledge.upsert("scenes", persisted)
            count += 1
        return count

    def analyze_episode(self, episode_id: str, *, force: bool = False) -> dict[str, Any]:
        episode = self.episodes.get(episode_id)
        if not bool(episode.get("approved", False)):
            raise ValueError(f"Episode is not approved for story analysis: {episode_id}")
        text = self.episodes.script(episode_id).strip()
        if not text:
            raise ValueError(f"Approved episode has no script text: {episode_id}")
        script_hash = self._script_hash(text)
        existing = self._analysis_record(episode_id)
        if existing and not force and str(existing.get("script_sha256", "")) == script_hash:
            return dict(existing)

        response = self.ai_manager.execute_prompt(
            "story_intelligence",
            {
                "episode_id": episode_id,
                "title": str(episode.get("title", episode_id)),
                "text": text,
            },
            provider_id=self.provider_id,
            model=self.model,
            temperature=0.1,
        )
        payload = self._parse_result(response.text)

        counts = {
            "characters": self._persist_named_entities("characters", "character", self._as_list(payload.get("characters")), episode_id),
            "locations": self._persist_named_entities("locations", "location", self._as_list(payload.get("locations")), episode_id),
            "objects": self._persist_named_entities("objects", "object", self._as_list(payload.get("objects")), episode_id),
            "relationships": self._persist_relationships(self._as_list(payload.get("relationships")), episode_id),
            "events": self._persist_events(self._as_list(payload.get("events")), episode_id),
            "scenes": self._persist_scenes(self._as_list(payload.get("scene_candidates", payload.get("scenes"))), episode_id),
        }

        analysis = {
            "id": f"analysis_{episode_id}",
            "episode_id": episode_id,
            "script_sha256": script_hash,
            "analyzed_at": datetime.now().isoformat(),
            "provider": str(getattr(response, "provider", "") or self.provider_id),
            "model": str(getattr(response, "model", "") or self.model),
            "genre": payload.get("genre", ""),
            "time_period": payload.get("time_period", ""),
            "mood": payload.get("mood", ""),
            "counts": counts,
        }
        self.knowledge.upsert("analyses", analysis)
        return analysis

    def analyze_approved_episodes(self, *, force: bool = False, progress=None) -> list[dict[str, Any]]:
        approved = self.episodes.approved()
        results: list[dict[str, Any]] = []
        total = len(approved)
        for index, episode in enumerate(approved, start=1):
            episode_id = str(episode.get("episode_id", ""))
            if not episode_id:
                continue
            result = self.analyze_episode(episode_id, force=force)
            results.append(result)
            if progress:
                progress(round(index / max(1, total) * 100), f"Analyzed story episode {index} of {total}")
        return results
