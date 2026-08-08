from __future__ import annotations

from collections.abc import Callable

from .exceptions import AIProviderNotFoundError
from .provider import AIProvider


ProviderFactory = Callable[[], AIProvider]


class AIProviderRegistry:
    """Registry of provider factories keyed by stable provider IDs."""

    def __init__(self):
        self._factories: dict[str, ProviderFactory] = {}

    def register(self, provider_id: str, factory: ProviderFactory, *, replace: bool = False) -> None:
        key = str(provider_id).strip().lower()
        if not key:
            raise ValueError("Provider ID cannot be empty.")
        if key in self._factories and not replace:
            raise ValueError(f"AI provider already registered: {key}")
        self._factories[key] = factory

    def unregister(self, provider_id: str) -> bool:
        return self._factories.pop(str(provider_id).strip().lower(), None) is not None

    def create(self, provider_id: str) -> AIProvider:
        key = str(provider_id).strip().lower()
        factory = self._factories.get(key)
        if factory is None:
            raise AIProviderNotFoundError(f"AI provider is not registered: {key}")
        return factory()

    def contains(self, provider_id: str) -> bool:
        return str(provider_id).strip().lower() in self._factories

    def providers(self) -> list[str]:
        return sorted(self._factories)
