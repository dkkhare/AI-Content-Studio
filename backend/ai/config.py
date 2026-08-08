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
    provider_models: dict[str, str] = field(default_factory=dict)

    def model_for(self, provider_id: str) -> str:
        return self.provider_models.get(str(provider_id).strip().lower(), self.default_model)

    @classmethod
    def from_environment(cls) -> "AIConfig":
        provider = os.getenv("AI_CONTENT_STUDIO_AI_PROVIDER", "").strip()
        model = os.getenv("AI_CONTENT_STUDIO_AI_MODEL", "").strip()
        order = [item.strip() for item in os.getenv("AI_CONTENT_STUDIO_AI_FAILOVER", "").split(",") if item.strip()]
        provider_models = {
            key: value for key, value in {
                "openai": os.getenv("OPENAI_DEFAULT_MODEL", "").strip(),
                "gemini": os.getenv("GEMINI_DEFAULT_MODEL", "").strip(),
                "ollama": os.getenv("OLLAMA_DEFAULT_MODEL", "").strip(),
            }.items() if value
        }
        try:
            timeout = float(os.getenv("AI_CONTENT_STUDIO_AI_TIMEOUT", "60"))
        except ValueError:
            timeout = 60.0
        return cls(provider, model, max(1.0, timeout), order, provider_models)
