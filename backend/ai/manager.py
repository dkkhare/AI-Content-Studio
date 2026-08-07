from __future__ import annotations

from collections.abc import Iterable

from .config import AIConfig
from .exceptions import AIAllProvidersFailedError, AIConfigurationError, AIError
from .models import AIRequest, AIResponse, AIStreamChunk
from .registry import AIProviderRegistry
from .usage import AIUsageTracker


class AIManager:
    """Central provider-neutral AI orchestration service."""

    def __init__(
        self,
        registry: AIProviderRegistry | None = None,
        config: AIConfig | None = None,
        usage: AIUsageTracker | None = None,
    ):
        self.registry = registry or AIProviderRegistry()
        self.config = config or AIConfig.from_environment()
        self.usage = usage or AIUsageTracker()

    def _provider_chain(self, provider_id: str | None = None) -> list[str]:
        chain: list[str] = []
        if provider_id:
            chain.append(str(provider_id).strip())
        elif self.config.default_provider:
            chain.append(self.config.default_provider)
        chain.extend(self.config.provider_order)

        deduped: list[str] = []
        seen: set[str] = set()
        for item in chain:
            key = item.strip().lower()
            if key and key not in seen:
                seen.add(key)
                deduped.append(key)
        if not deduped:
            available = self.registry.providers()
            if len(available) == 1:
                return available
            raise AIConfigurationError(
                "No AI provider selected. Configure a default provider or pass provider_id."
            )
        return deduped

    def generate(self, request: AIRequest, *, provider_id: str | None = None) -> AIResponse:
        errors: list[str] = []
        for key in self._provider_chain(provider_id):
            try:
                provider = self.registry.create(key)
                if not provider.configured():
                    raise AIConfigurationError(f"AI provider is not configured: {key}")
                if not request.model and self.config.default_model:
                    request.model = self.config.default_model
                response = provider.generate(request)
                self.usage.record(response.provider or key, response.model, response.usage)
                return response
            except AIError as exc:
                errors.append(f"{key}: {exc}")
            except Exception as exc:
                errors.append(f"{key}: {exc}")
        raise AIAllProvidersFailedError("All AI providers failed: " + " | ".join(errors))

    def stream(
        self,
        request: AIRequest,
        *,
        provider_id: str | None = None,
    ) -> Iterable[AIStreamChunk]:
        errors: list[str] = []
        for key in self._provider_chain(provider_id):
            try:
                provider = self.registry.create(key)
                if not provider.configured():
                    raise AIConfigurationError(f"AI provider is not configured: {key}")
                if not request.model and self.config.default_model:
                    request.model = self.config.default_model
                for chunk in provider.stream(request):
                    if chunk.done and chunk.usage is not None:
                        self.usage.record(chunk.provider or key, chunk.model, chunk.usage)
                    yield chunk
                return
            except AIError as exc:
                errors.append(f"{key}: {exc}")
            except Exception as exc:
                errors.append(f"{key}: {exc}")
        raise AIAllProvidersFailedError("All AI providers failed: " + " | ".join(errors))
