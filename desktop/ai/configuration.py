from __future__ import annotations

import os
from dataclasses import dataclass, field

from backend.ai import AIConfig


PROVIDER_SECRET_ENV = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
}
PROVIDER_MODEL_ENV = {
    "openai": "OPENAI_DEFAULT_MODEL",
    "gemini": "GEMINI_DEFAULT_MODEL",
    "ollama": "OLLAMA_DEFAULT_MODEL",
}


@dataclass(slots=True)
class AIProfile:
    provider: str = "ollama"
    model: str = ""
    failover: list[str] = field(default_factory=list)
    timeout_seconds: float = 60.0

    def normalized(self) -> "AIProfile":
        provider = self.provider.strip().lower()
        if provider not in {"openai", "gemini", "ollama"}:
            raise ValueError(f"Unsupported AI provider: {provider}")
        order, seen = [], {provider}
        for value in self.failover:
            key = str(value).strip().lower()
            if key in {"openai", "gemini", "ollama"} and key not in seen:
                seen.add(key)
                order.append(key)
        return AIProfile(provider, self.model.strip(), order, max(1.0, float(self.timeout_seconds)))

    def to_ai_config(self) -> AIConfig:
        value = self.normalized()
        models = {value.provider: value.model} if value.model else {}
        return AIConfig(
            default_provider=value.provider,
            default_model=value.model,
            timeout_seconds=value.timeout_seconds,
            provider_order=value.failover,
            provider_models=models,
        )


class AISettingsStore:
    """Persists non-secret desktop AI preferences through SettingsManager."""

    PREFIX = "ai/"

    def __init__(self, settings):
        self.settings = settings

    def load(self) -> AIProfile:
        raw_failover = self.settings.value(self.PREFIX + "failover", [])
        if isinstance(raw_failover, str):
            raw_failover = [item.strip() for item in raw_failover.split(",") if item.strip()]
        try:
            timeout = float(self.settings.value(self.PREFIX + "timeout_seconds", 60.0))
        except (TypeError, ValueError):
            timeout = 60.0
        return AIProfile(
            provider=str(self.settings.value(self.PREFIX + "provider", "ollama")),
            model=str(self.settings.value(self.PREFIX + "model", "")),
            failover=list(raw_failover or []),
            timeout_seconds=timeout,
        ).normalized()

    def save(self, profile: AIProfile) -> AIProfile:
        value = profile.normalized()
        self.settings.set_value(self.PREFIX + "provider", value.provider)
        self.settings.set_value(self.PREFIX + "model", value.model)
        self.settings.set_value(self.PREFIX + "failover", value.failover)
        self.settings.set_value(self.PREFIX + "timeout_seconds", value.timeout_seconds)
        self.settings.sync()
        return value

    @staticmethod
    def secret_environment(provider: str) -> str | None:
        return PROVIDER_SECRET_ENV.get(str(provider).strip().lower())

    def set_session_secret(self, provider: str, secret: str) -> None:
        env_name = self.secret_environment(provider)
        if not env_name:
            return
        value = str(secret).strip()
        if value:
            os.environ[env_name] = value
        else:
            os.environ.pop(env_name, None)

    def has_session_secret(self, provider: str) -> bool:
        env_name = self.secret_environment(provider)
        return bool(env_name and os.getenv(env_name))
