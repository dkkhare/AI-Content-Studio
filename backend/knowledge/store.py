from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class KnowledgeStore:
    """Persisted JSON knowledge base for one AI Content Studio project."""

    DIRECTORY_NAME = "knowledge"
    FILE_DEFAULTS: dict[str, Any] = {
        "book.json": {},
        "characters.json": [],
        "locations.json": [],
        "objects.json": [],
        "timeline.json": [],
        "relationships.json": [],
        "glossary.json": [],
        "pronunciation.json": [],
        "style.json": {},
        "scenes.json": [],
        "prompts.json": [],
        "assets.json": [],
    }

    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root).resolve()
        self.root = self.project_root / self.DIRECTORY_NAME

    def initialize(self) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        for filename, default in self.FILE_DEFAULTS.items():
            path = self.root / filename
            if not path.exists():
                self._write_path(path, default)
        return self.root

    def path(self, name: str) -> Path:
        filename = name if name.endswith(".json") else f"{name}.json"
        if filename not in self.FILE_DEFAULTS:
            raise KeyError(f"Unknown knowledge collection: {name}")
        return self.root / filename

    def read(self, name: str) -> Any:
        path = self.path(name)
        if not path.exists():
            self.initialize()
        try:
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid knowledge JSON: {path}") from exc

    def write(self, name: str, value: Any) -> Path:
        self.initialize()
        path = self.path(name)
        self._validate_shape(path.name, value)
        self._write_path(path, value)
        return path

    def update_mapping(self, name: str, values: dict[str, Any]) -> dict[str, Any]:
        current = self.read(name)
        if not isinstance(current, dict):
            raise TypeError(f"Knowledge collection {name} is not a mapping.")
        current.update(values)
        self.write(name, current)
        return current

    def append(self, name: str, item: dict[str, Any]) -> list[dict[str, Any]]:
        current = self.read(name)
        if not isinstance(current, list):
            raise TypeError(f"Knowledge collection {name} is not a list.")
        current.append(dict(item))
        self.write(name, current)
        return current

    def upsert(self, name: str, item: dict[str, Any], *, id_key: str = "id") -> dict[str, Any]:
        if id_key not in item or not str(item[id_key]).strip():
            raise ValueError(f"Knowledge item requires non-empty {id_key!r}.")
        current = self.read(name)
        if not isinstance(current, list):
            raise TypeError(f"Knowledge collection {name} is not a list.")
        identifier = str(item[id_key])
        for index, existing in enumerate(current):
            if isinstance(existing, dict) and str(existing.get(id_key, "")) == identifier:
                merged = dict(existing)
                merged.update(item)
                current[index] = merged
                self.write(name, current)
                return merged
        current.append(dict(item))
        self.write(name, current)
        return dict(item)

    def counts(self) -> dict[str, int]:
        result: dict[str, int] = {}
        for filename in self.FILE_DEFAULTS:
            key = filename.removesuffix(".json")
            value = self.read(key)
            result[key] = len(value) if isinstance(value, (list, dict)) else 0
        return result

    @staticmethod
    def _write_path(path: Path, value: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(value, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(path)

    def _validate_shape(self, filename: str, value: Any) -> None:
        default = self.FILE_DEFAULTS[filename]
        if isinstance(default, list) and not isinstance(value, list):
            raise TypeError(f"{filename} must contain a JSON list.")
        if isinstance(default, dict) and not isinstance(value, dict):
            raise TypeError(f"{filename} must contain a JSON object.")
