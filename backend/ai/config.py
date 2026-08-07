from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(slots=True)
class AIConfig:
    """Environment-backed AI configuration with no project-secret persistence."""

    default_provider: str = ""
    default_model: str = ""
    timeout_seconds: float = 60.0
    provider_order: list[str] = field(default_factory=list)

    @classmethod
    def from_environment(cls) -> "AIConfig":
        provider = os.getenv("AI_CONTENT_STUDIO_AI_PROVIDER", "").strip()
        model = os.getenv("AI_CONTENT_STUDIO_AI_MODEL", "").strip()
        raw_order = os.getenv("AI_CONTENT_STUDIO_AI_FAILOVER", "").strip()
        order = [item.strip() for item in raw_order.split(",") if item.strip()]
        try:
            timeout = float(os.getenv("AI_CONTENT_STUDIO_AI_TIMEOUT", "60"))
        except ValueError:
            timeout = 60.0
        return cls(
            default_provider=provider,
            default_model=model,
            timeout_seconds=max(1.0, timeout),
            provider_order=order,
        )
