from __future__ import annotations

import threading
from collections.abc import Callable

from .control import PipelineControl
from .exceptions import PipelineBusyError
from .pipeline import ProcessingPipeline


class PipelineRunner:
    """Runs a processing pipeline synchronously or on a worker thread."""

    def __init__(self, pipeline: ProcessingPipeline | None = None):
        self.pipeline = pipeline or ProcessingPipeline()
        self.control = PipelineControl()
        self._thread: threading.Thread | None = None
        self._lock = threading.RLock()
        self._last_state = None
        self._last_error: Exception | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def paused(self) -> bool:
        return self.control.paused

    @property
    def last_state(self):
        return self._last_state

    @property
    def last_error(self) -> Exception | None:
        return self._last_error

    def add_stage(self, stage):
        return self.pipeline.add_stage(stage)

    def run(self, context, *, progress_callback=None, resume: bool = True):
        with self._lock:
            if self.running:
                raise PipelineBusyError("Pipeline runner is already active.")
            self.control = PipelineControl()
            self._last_error = None

        try:
            self._last_state = self.pipeline.execute(
                context,
                control=self.control,
                progress_callback=progress_callback,
                resume=resume,
            )
            return self._last_state
        except Exception as exc:
            self._last_error = exc
            raise

    def start(
        self,
        context,
        *,
        progress_callback=None,
        finished_callback: Callable[[object], None] | None = None,
        error_callback: Callable[[Exception], None] | None = None,
        resume: bool = True,
        daemon: bool = True,
    ) -> threading.Thread:
        with self._lock:
            if self.running:
                raise PipelineBusyError("Pipeline runner is already active.")
            self.control = PipelineControl()
            self._last_error = None

            def worker() -> None:
                try:
                    self._last_state = self.pipeline.execute(
                        context,
                        control=self.control,
                        progress_callback=progress_callback,
                        resume=resume,
                    )
                    if finished_callback:
                        finished_callback(self._last_state)
                except Exception as exc:
                    self._last_error = exc
                    if error_callback:
                        error_callback(exc)
                finally:
                    with self._lock:
                        self._thread = None

            self._thread = threading.Thread(
                target=worker,
                name="ai-content-studio-pipeline",
                daemon=daemon,
            )
            self._thread.start()
            return self._thread

    def pause(self) -> bool:
        if not self.running:
            return False
        self.control.pause()
        return True

    def resume(self) -> bool:
        if not self.running:
            return False
        self.control.resume()
        return True

    def cancel(self) -> bool:
        if not self.running:
            return False
        self.control.cancel()
        return True

    def wait(self, timeout: float | None = None) -> bool:
        thread = self._thread
        if thread is None:
            return True
        thread.join(timeout)
        return not thread.is_alive()
