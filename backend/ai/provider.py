from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from .models import AIRequest, AIResponse, AIStreamChunk


class AIProvider(ABC):
    """Provider-neutral interface used by AI-Content-Studio."""

    provider_id = "base"

    @abstractmethod
    def configured(self) -> bool:
        """Return whether the provider has the configuration needed to run."""

    @abstractmethod
    def generate(self, request: AIRequest) -> AIResponse:
        """Generate a complete response."""

    def stream(self, request: AIRequest) -> Iterable[AIStreamChunk]:
        response = self.generate(request)
        yield AIStreamChunk(
            text=response.text,
            provider=response.provider,
            model=response.model,
            done=True,
            usage=response.usage,
            raw=response.raw,
        )

    def list_models(self) -> list[str]:
        return []

    def capabilities(self) -> set[str]:
        return {"text"}

    def supports(self, capability: str) -> bool:
        return str(capability).strip().lower() in {
            item.lower() for item in self.capabilities()
        }

    def health_check(self) -> tuple[bool, str]:
        if not self.configured():
            return False, f"{self.provider_id} is not configured"
        return True, f"{self.provider_id} is configured"
