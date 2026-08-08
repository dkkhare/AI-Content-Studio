from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.episodes import EpisodeReviewStore


class ReleaseManager:
    """Provider-neutral release state for approved, publish-ready episodes."""

    VALID_STATES = {"draft", "ready", "published", "failed"}

    def __init__(self, project_root: str | Path):
        self.root = Path(project_root).resolve()
        self.episodes = EpisodeReviewStore(self.root)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _publish_dir(self, episode_id: str) -> Path:
        return self.root / "segments" / episode_id / "publish"

    def _release_path(self, episode_id: str) -> Path:
        return self._publish_dir(episode_id) / "release.json"

    def _manifest_path(self, episode_id: str) -> Path:
        return self._publish_dir(episode_id) / "manifest.json"

    def manifest(self, episode_id: str) -> dict[str, Any]:
        path = self._manifest_path(episode_id)
        if not path.exists():
            raise ValueError(f"Publishing manifest is missing for {episode_id}.")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"Publishing manifest is invalid for {episode_id}.")
        return payload

    def validation(self, episode_id: str) -> dict[str, Any]:
        episode = self.episodes.get(episode_id)
        approved = bool(episode.get("approved", False))
        manifest_path = self._manifest_path(episode_id)
        manifest_exists = manifest_path.exists()
        video_path = ""
        thumbnail_path = ""
        if manifest_exists:
            try:
                manifest = self.manifest(episode_id)
                files = manifest.get("files", {}) if isinstance(manifest.get("files"), dict) else {}
                video_path = str(files.get("video", ""))
                thumbnail_path = str(files.get("thumbnail", ""))
            except Exception:
                manifest_exists = False
        video_exists = bool(video_path) and (self.root / video_path).is_file()
        thumbnail_exists = bool(thumbnail_path) and (self.root / thumbnail_path).is_file()
        errors = []
        if not approved:
            errors.append("episode_not_approved")
        if not manifest_exists:
            errors.append("manifest_missing")
        if not video_exists:
            errors.append("final_video_missing")
        if not thumbnail_exists:
            errors.append("thumbnail_missing")
        return {
            "episode_id": episode_id,
            "approved": approved,
            "manifest_exists": manifest_exists,
            "video_exists": video_exists,
            "thumbnail_exists": thumbnail_exists,
            "video_path": video_path,
            "thumbnail_path": thumbnail_path,
            "ready": not errors,
            "errors": errors,
        }

    def _default_record(self, episode_id: str) -> dict[str, Any]:
        episode = self.episodes.get(episode_id)
        return {
            "schema_version": 1,
            "episode_id": episode_id,
            "title": str(episode.get("title", episode_id)),
            "state": "draft",
            "destination": "",
            "external_id": "",
            "external_url": "",
            "error": "",
            "created_at": self._now(),
            "updated_at": self._now(),
            "history": [],
        }

    def get(self, episode_id: str) -> dict[str, Any]:
        path = self._release_path(episode_id)
        if not path.exists():
            return self._default_record(episode_id)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"Release record is invalid for {episode_id}.")
        payload.setdefault("history", [])
        payload.setdefault("state", "draft")
        return payload

    def _save(self, episode_id: str, record: dict[str, Any]) -> dict[str, Any]:
        folder = self._publish_dir(episode_id)
        folder.mkdir(parents=True, exist_ok=True)
        record["updated_at"] = self._now()
        self._release_path(episode_id).write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return record

    def _transition(self, episode_id: str, state: str, *, note: str = "", **fields) -> dict[str, Any]:
        if state not in self.VALID_STATES:
            raise ValueError(f"Unsupported release state: {state}")
        record = self.get(episode_id)
        previous = str(record.get("state", "draft"))
        entry = {
            "from": previous,
            "to": state,
            "at": self._now(),
            "note": str(note or ""),
        }
        record.update(fields)
        record["state"] = state
        record.setdefault("history", []).append(entry)
        return self._save(episode_id, record)

    def mark_ready(self, episode_id: str, *, note: str = "") -> dict[str, Any]:
        check = self.validation(episode_id)
        if not check["ready"]:
            raise ValueError(
                "Episode is not publish-ready: " + ", ".join(check["errors"])
            )
        return self._transition(
            episode_id,
            "ready",
            note=note,
            error="",
            validation=check,
            ready_at=self._now(),
        )

    def mark_draft(self, episode_id: str, *, note: str = "") -> dict[str, Any]:
        return self._transition(episode_id, "draft", note=note, error="")

    def mark_failed(self, episode_id: str, error: str, *, note: str = "") -> dict[str, Any]:
        message = str(error or "").strip()
        if not message:
            raise ValueError("A release failure requires an error message.")
        return self._transition(episode_id, "failed", note=note, error=message)

    def mark_published(
        self,
        episode_id: str,
        *,
        destination: str,
        external_id: str = "",
        external_url: str = "",
        note: str = "",
    ) -> dict[str, Any]:
        record = self.get(episode_id)
        if str(record.get("state", "draft")) != "ready":
            raise ValueError("Episode must be Ready before it can be marked Published.")
        target = str(destination or "").strip()
        if not target:
            raise ValueError("Published releases require a destination.")
        return self._transition(
            episode_id,
            "published",
            note=note,
            destination=target,
            external_id=str(external_id or "").strip(),
            external_url=str(external_url or "").strip(),
            error="",
            published_at=self._now(),
        )

    def items(self) -> list[dict[str, Any]]:
        rows = []
        for episode in self.episodes.approved():
            episode_id = str(episode.get("episode_id", ""))
            if not episode_id:
                continue
            record = self.get(episode_id)
            record["validation"] = self.validation(episode_id)
            rows.append(record)
        return rows

    def summary(self) -> dict[str, int]:
        result = {"draft": 0, "ready": 0, "published": 0, "failed": 0, "total": 0}
        for item in self.items():
            state = str(item.get("state", "draft"))
            if state not in result:
                state = "draft"
            result[state] += 1
            result["total"] += 1
        return result
