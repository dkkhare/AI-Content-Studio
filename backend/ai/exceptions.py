from __future__ import annotations


class AIError(RuntimeError):
    """Base error for AI provider and orchestration failures."""


class AIConfigurationError(AIError):
    """Raised when a provider is missing required configuration."""


class AIProviderError(AIError):
    """Raised when an AI provider request fails."""


class AIProviderNotFoundError(AIError):
    """Raised when a requested provider is not registered."""


class AIAllProvidersFailedError(AIError):
    """Raised when every provider in a failover chain fails."""
