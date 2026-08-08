from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class PipelineState:
    schema_version: int = 2
    status: str = "idle"
    current_stage_index: int = 0
    current_stage_id: str = ""
    completed_stage_ids: list[str] = field(default_factory=list)
    stage_attempts: dict[str, int] = field(default_factory=dict)
    failures: list[dict[str, Any]] = field(default_factory=list)
    error_message: str = ""
    started_at: str = ""
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finished_at: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def record_attempt(self, stage_id: str) -> int:
        key = str(stage_id or "")
        self.stage_attempts[key] = int(self.stage_attempts.get(key, 0)) + 1
        return self.stage_attempts[key]

    def record_failure(self, *, stage_id: str, stage_name: str, error: BaseException) -> dict[str, Any]:
        entry = {
            "stage_id": str(stage_id or ""),
            "stage_name": str(stage_name or ""),
            "attempt": int(self.stage_attempts.get(str(stage_id or ""), 0)),
            "error_type": type(error).__name__,
            "message": str(error),
            "at": datetime.now(timezone.utc).isoformat(),
        }
        self.failures.append(entry)
        return entry

    def to_dict(self) -> dict:
        self.touch()
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PipelineState":
        allowed = cls.__dataclass_fields__.keys()
        values = {key: value for key, value in data.items() if key in allowed}
        return cls(**values)


class PipelineStateStore:
    DIRECTORY = ".pipeline"
    FILE_NAME = "state.json"
    BACKUP_FILE_NAME = "state.bak.json"

    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root).resolve()
        self.directory = self.project_root / self.DIRECTORY
        self.path = self.directory / self.FILE_NAME
        self.backup_path = self.directory / self.BACKUP_FILE_NAME

    def exists(self) -> bool:
        return self.path.is_file() or self.backup_path.is_file()

    @staticmethod
    def _read(path: Path) -> PipelineState:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, dict):
            raise ValueError(f"Pipeline state must contain a JSON object: {path}")
        return PipelineState.from_dict(data)

    def load(self) -> PipelineState:
        if self.path.is_file():
            try:
                return self._read(self.path)
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                if self.backup_path.is_file():
                    return self._read(self.backup_path)
                raise
        if self.backup_path.is_file():
            return self._read(self.backup_path)
        return PipelineState()

    def save(self, state: PipelineState) -> Path:
        self.directory.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        with open(temporary, "w", encoding="utf-8") as file:
            json.dump(state.to_dict(), file, indent=2, ensure_ascii=False, default=str)
            file.flush()
        if self.path.is_file():
            try:
                self.backup_path.write_bytes(self.path.read_bytes())
            except OSError:
                pass
        temporary.replace(self.path)
        return self.path

    def clear(self) -> bool:
        removed = False
        for path in (self.path, self.backup_path):
            if path.exists():
                path.unlink()
                removed = True
        return removed
