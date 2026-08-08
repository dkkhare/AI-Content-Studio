"""Desktop UI package.

Keep package imports lightweight so individual windows, dialogs, and widgets can
be imported without initializing unrelated optional feature stacks.
"""

from __future__ import annotations

from typing import Any

__all__ = ["Workspace"]


def __getattr__(name: str) -> Any:
    if name == "Workspace":
        from .workspace import Workspace

        return Workspace
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
