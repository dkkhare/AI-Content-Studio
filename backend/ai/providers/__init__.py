from __future__ import annotations

from ..registry import AIProviderRegistry
from .gemini import GeminiProvider
from .ollama import OllamaProvider
from .openai import OpenAIProvider


def register_builtin_providers(
    registry: AIProviderRegistry,
    *,
    replace: bool = False,
) -> AIProviderRegistry:
    registry.register("openai", OpenAIProvider, replace=replace)
    registry.register("ollama", OllamaProvider, replace=replace)
    registry.register("gemini", GeminiProvider, replace=replace)
    return registry


def create_default_registry() -> AIProviderRegistry:
    return register_builtin_providers(AIProviderRegistry())


__all__ = [
    "GeminiProvider",
    "OllamaProvider",
    "OpenAIProvider",
    "create_default_registry",
    "register_builtin_providers",
]
