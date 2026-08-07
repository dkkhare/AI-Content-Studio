from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime


@dataclass
class PipelineProgress:
    stage_id: str = ""
    current_stage: str = ""
    stage_index: int = 0
    total_stages: int = 0
    stage_percent: int = 0
    percent: int = 0
    message: str = ""
    status: str = "idle"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def normalized(self) -> "PipelineProgress":
        self.stage_percent = max(0, min(100, int(self.stage_percent)))
        self.percent = max(0, min(100, int(self.percent)))
        return self

    def to_dict(self) -> dict:
        return asdict(self.normalized())
