from __future__ import annotations

from abc import ABC, abstractmethod


class TranslationProviderError(RuntimeError):
    """Raised when a translation provider cannot complete a request."""


class TranslationProvider(ABC):
    """Common interface for translation services used by the pipeline."""

    provider_id = "translation"

    @abstractmethod
    def translate(
        self,
        text: str,
        *,
        source_language: str | None = None,
        target_language: str | None = None,
    ) -> str:
        raise NotImplementedError
