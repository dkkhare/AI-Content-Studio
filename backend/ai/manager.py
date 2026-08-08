from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

from .config import AIConfig
from .exceptions import AIAllProvidersFailedError, AIConfigurationError, AIError, AIStreamInterruptedError
from .models import AIRequest, AIResponse, AIStreamChunk
from .prompts import PromptLibrary, create_builtin_library
from .registry import AIProviderRegistry
from .usage import AIUsageTracker


class AIManager:
    """Central provider-neutral AI orchestration service."""

    def __init__(self, registry=None, config=None, usage=None, prompt_library=None):
        if registry is None:
            from .providers import create_default_registry
            registry = create_default_registry()
        self.registry: AIProviderRegistry = registry
        self.config: AIConfig = config or AIConfig.from_environment()
        self.usage = usage or AIUsageTracker()
        self.prompt_library = prompt_library or create_builtin_library()

    def _provider_chain(self, provider_id: str | None = None) -> list[str]:
        chain = [provider_id] if provider_id else ([self.config.default_provider] if self.config.default_provider else [])
        chain.extend(self.config.provider_order)
        deduped, seen = [], set()
        for item in chain:
            key = str(item).strip().lower()
            if key and key not in seen:
                seen.add(key)
                deduped.append(key)
        if deduped:
            return deduped
        available = self.registry.providers()
        configured = []
        for key in available:
            try:
                if self.registry.create(key).configured():
                    configured.append(key)
            except Exception:
                continue
        if len(configured) == 1:
            return configured
        if len(available) == 1:
            return available
        raise AIConfigurationError("No AI provider selected. Configure a default provider or pass provider_id.")

    def _request_for(self, request: AIRequest, provider_id: str) -> AIRequest:
        """Build a provider-specific copy; never mutate the caller's request."""
        return replace(
            request,
            model=request.model or self.config.model_for(provider_id),
            messages=list(request.messages),
            metadata=dict(request.metadata),
        )

    def generate(self, request: AIRequest, *, provider_id: str | None = None) -> AIResponse:
        errors = []
        for key in self._provider_chain(provider_id):
            try:
                provider = self.registry.create(key)
                if not provider.configured():
                    raise AIConfigurationError(f"AI provider is not configured: {key}")
                response = provider.generate(self._request_for(request, key))
                self.usage.record(response.provider or key, response.model, response.usage)
                return response
            except AIError as exc:
                errors.append(f"{key}: {exc}")
            except Exception as exc:
                errors.append(f"{key}: {exc}")
        raise AIAllProvidersFailedError("All AI providers failed: " + " | ".join(errors))

    def stream(self, request: AIRequest, *, provider_id: str | None = None) -> Iterable[AIStreamChunk]:
        errors = []
        for key in self._provider_chain(provider_id):
            emitted = False
            try:
                provider = self.registry.create(key)
                if not provider.configured():
                    raise AIConfigurationError(f"AI provider is not configured: {key}")
                for chunk in provider.stream(self._request_for(request, key)):
                    emitted = emitted or bool(chunk.text)
                    if chunk.done and chunk.usage is not None:
                        self.usage.record(chunk.provider or key, chunk.model, chunk.usage)
                    yield chunk
                return
            except Exception as exc:
                if emitted:
                    raise AIStreamInterruptedError(
                        f"{key} stream failed after emitting output: {exc}"
                    ) from exc
                errors.append(f"{key}: {exc}")
        raise AIAllProvidersFailedError("All AI providers failed: " + " | ".join(errors))

    def execute_prompt(self, template: str, variables: dict | None = None, *, version=None,
                       provider_id=None, model="", temperature=None, max_output_tokens=None) -> AIResponse:
        prompt = self.prompt_library.get(template, version)
        request = prompt.render(
            variables, model=model, temperature=temperature,
            max_output_tokens=max_output_tokens,
            metadata={"prompt": prompt.name, "prompt_version": prompt.version},
        )
        return self.generate(request, provider_id=provider_id)

    def stream_prompt(self, template: str, variables: dict | None = None, *, version=None,
                      provider_id=None, model="", temperature=None, max_output_tokens=None):
        prompt = self.prompt_library.get(template, version)
        request = prompt.render(
            variables, model=model, temperature=temperature,
            max_output_tokens=max_output_tokens,
            metadata={"prompt": prompt.name, "prompt_version": prompt.version},
        )
        yield from self.stream(request, provider_id=provider_id)

    def list_prompts(self) -> list[str]:
        return self.prompt_library.names()

    def get_prompt(self, name: str, version: str | None = None):
        return self.prompt_library.get(name, version)

    def providers(self) -> list[str]:
        return self.registry.providers()

    def capabilities(self, provider_id: str) -> set[str]:
        return set(self.registry.create(provider_id).capabilities())

    def health_check(self, provider_id: str) -> tuple[bool, str]:
        return self.registry.create(provider_id).health_check()

    def list_models(self, provider_id: str) -> list[str]:
        provider = self.registry.create(provider_id)
        if not provider.configured():
            raise AIConfigurationError(f"AI provider is not configured: {provider_id}")
        return provider.list_models()
