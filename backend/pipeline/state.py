from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class PipelineState:
    status: str = "idle"
    current_stage_index: int = 0
    current_stage_id: str = ""
    completed_stage_ids: list[str] = field(default_factory=list)
    error_message: str = ""
    started_at: str = ""
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    finished_at: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    def touch(self) -> None:
        self.updated_at = datetime.now().isoformat()

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

    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root).resolve()
        self.directory = self.project_root / self.DIRECTORY
        self.path = self.directory / self.FILE_NAME

    def exists(self) -> bool:
        return self.path.is_file()

    def load(self) -> PipelineState:
        if not self.exists():
            return PipelineState()
        with open(self.path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return PipelineState.from_dict(data)

    def save(self, state: PipelineState) -> Path:
        self.directory.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        with open(temporary, "w", encoding="utf-8") as file:
            json.dump(state.to_dict(), file, indent=2, ensure_ascii=False, default=str)
        temporary.replace(self.path)
        return self.path

    def clear(self) -> bool:
        if not self.path.exists():
            return False
        self.path.unlink()
        return True
