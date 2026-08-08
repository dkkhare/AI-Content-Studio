from __future__ import annotations

from collections.abc import Iterable

from .models import AIStreamChunk


def collect_stream(chunks: Iterable[AIStreamChunk]) -> str:
    """Collect streamed text chunks into one response string."""
    return "".join(chunk.text for chunk in chunks if chunk.text)
