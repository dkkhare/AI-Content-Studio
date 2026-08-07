from __future__ import annotations

import threading
import time

from .exceptions import PipelineCancelled


class PipelineControl:
    """Thread-safe pause/resume/cancel control shared with stages."""

    def __init__(self):
        self._cancelled = threading.Event()
        self._paused = threading.Event()

    @property
    def cancelled(self) -> bool:
        return self._cancelled.is_set()

    @property
    def paused(self) -> bool:
        return self._paused.is_set()

    def cancel(self) -> None:
        self._cancelled.set()
        self._paused.clear()

    def pause(self) -> None:
        if not self.cancelled:
            self._paused.set()

    def resume(self) -> None:
        self._paused.clear()

    def checkpoint(self, sleep_seconds: float = 0.05) -> None:
        if self.cancelled:
            raise PipelineCancelled("Pipeline cancelled.")
        while self.paused:
            if self.cancelled:
                raise PipelineCancelled("Pipeline cancelled.")
            time.sleep(max(0.01, sleep_seconds))
