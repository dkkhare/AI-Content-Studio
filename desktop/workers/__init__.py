"""Background worker package with lazy compatibility exports."""

from __future__ import annotations

from typing import Any

__all__ = ["TTSWorker"]


def __getattr__(name: str) -> Any:
    if name == "TTSWorker":
        from .tts_worker import TTSWorker

        return TTSWorker
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
