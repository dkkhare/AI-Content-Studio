from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable


class EpisodeReviewStore:
    """Read and update the persisted episode review manifest."""

    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root).resolve()
        self.manifest_path = self.project_root / "segments" / "episodes.json"

    def exists(self) -> bool:
        return self.manifest_path.exists() and self.manifest_path.is_file()

    def load(self) -> dict:
        if not self.exists():
            return {"episodes": []}
        with self.manifest_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            raise ValueError("Episode manifest must contain a JSON object.")
        episodes = payload.get("episodes")
        if not isinstance(episodes, list):
            payload["episodes"] = []
        return payload

    def save(self, payload: dict) -> None:
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def episodes(self) -> list[dict]:
        return list(self.load().get("episodes", []))

    def get(self, episode_id: str) -> dict:
        for episode in self.episodes():
            if str(episode.get("episode_id", "")) == episode_id:
                return episode
        raise KeyError(f"Unknown episode: {episode_id}")

    def _update(self, episode_id: str, updater: Callable[[dict, dict], None]) -> dict:
        payload = self.load()
        for episode in payload.get("episodes", []):
            if str(episode.get("episode_id", "")) == episode_id:
                updater(episode, payload)
                self.save(payload)
                return episode
        raise KeyError(f"Unknown episode: {episode_id}")

    def script_path(self, episode: dict) -> Path:
        raw = str(episode.get("text_file", "") or "")
        if not raw:
            raise ValueError("Episode has no script file.")
        path = Path(raw)
        return path if path.is_absolute() else self.project_root / path

    def script(self, episode_id: str) -> str:
        path = self.script_path(self.get(episode_id))
        return path.read_text(encoding="utf-8") if path.exists() else ""

    @staticmethod
    def _word_count(text: str) -> int:
        return len(re.findall(r"\S+", text, flags=re.UNICODE))

    def edit(self, episode_id: str, *, title: str, text: str) -> dict:
        clean_title = str(title).strip() or episode_id.replace("_", " ").title()
        clean_text = str(text).strip()
        if not clean_text:
            raise ValueError("Episode script cannot be empty.")

        def apply(episode: dict, payload: dict) -> None:
            path = self.script_path(episode)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(clean_text, encoding="utf-8")
            words = self._word_count(clean_text)
            wpm = max(1.0, float(payload.get("words_per_minute", 130.0) or 130.0))
            episode["title"] = clean_title
            episode["word_count"] = words
            episode["estimated_minutes"] = round(words / wpm, 2)
            episode["approved"] = False
            episode["status"] = "edited"

        return self._update(episode_id, apply)

    def approve(self, episode_id: str) -> dict:
        return self._update(
            episode_id,
            lambda episode, payload: episode.update(
                {"approved": True, "status": "approved"}
            ),
        )

    def skip(self, episode_id: str) -> dict:
        return self._update(
            episode_id,
            lambda episode, payload: episode.update(
                {"approved": False, "status": "skipped"}
            ),
        )

    def request_regeneration(self, episode_id: str) -> dict:
        return self._update(
            episode_id,
            lambda episode, payload: episode.update(
                {"approved": False, "status": "regenerate_requested"}
            ),
        )

    def replace_regenerated_text(self, episode_id: str, text: str) -> dict:
        current = self.get(episode_id)
        return self.edit(
            episode_id,
            title=str(current.get("title", episode_id)),
            text=text,
        )

    def pending(self) -> list[dict]:
        return [
            episode
            for episode in self.episodes()
            if not bool(episode.get("approved", False))
            and str(episode.get("status", "planned")) != "skipped"
        ]

    def review_complete(self) -> bool:
        episodes = self.episodes()
        return bool(episodes) and not self.pending()

    def approved(self) -> list[dict]:
        return [episode for episode in self.episodes() if bool(episode.get("approved", False))]
