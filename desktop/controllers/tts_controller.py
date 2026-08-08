from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import QObject, QThread, Signal

from desktop.workers.tts_worker import TTSWorker


class TTSController(QObject):
    """Own one background narration job and its QThread lifecycle."""

    generation_started = Signal()
    generation_progress = Signal(object)
    generation_finished = Signal(object)
    generation_failed = Signal(str)
    generation_cancelled = Signal()
    log_message = Signal(str)

    def __init__(self, parent=None, worker_factory: Callable[[], TTSWorker] = TTSWorker):
        super().__init__(parent)
        self.thread: Optional[QThread] = None
        self.worker: Optional[TTSWorker] = None
        self._worker_factory = worker_factory
        self._running = False
        self._last_session = None
        self._last_output = ""
        self._voice_profiles: list[str] = []

    def generate(
        self,
        reference_audio: str,
        reference_text: str,
        text: str,
        output_directory: str,
        *,
        voice_name: str = "",
        language: str = "en",
    ) -> None:
        if self._running:
            raise RuntimeError("A narration job is already running.")
        if not str(text).strip():
            raise ValueError("Text cannot be empty.")
        if not str(reference_audio).strip():
            raise ValueError("Reference audio is required.")
        if not str(reference_text).strip():
            raise ValueError("Reference transcript is required.")

        output = str(Path(output_directory))
        Path(output).mkdir(parents=True, exist_ok=True)
        self._last_session = None
        self._last_output = ""
        self._create_worker()
        assert self.worker is not None and self.thread is not None
        self.worker.configure(
            reference_audio=reference_audio,
            reference_text=reference_text,
            text=text,
            output_directory=output,
            voice_name=voice_name,
            language=language,
        )
        self._running = True
        self.thread.start()

    def _create_worker(self) -> None:
        self.shutdown(wait=True)
        thread = QThread(self)
        worker = self._worker_factory()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.started.connect(self._on_started)
        worker.progress.connect(self.generation_progress)
        worker.finished.connect(self._on_finished)
        worker.failed.connect(self._on_failed)
        worker.cancelled.connect(self._on_cancelled)
        worker.log.connect(self.log_message)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.cancelled.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(self._on_thread_finished)
        self.thread = thread
        self.worker = worker

    def _on_started(self) -> None:
        self.log_message.emit("TTS generation started.")
        self.generation_started.emit()

    def _on_finished(self, session) -> None:
        self._running = False
        self._last_session = session
        self._last_output = getattr(session, "output_file", "") if session else ""
        self.log_message.emit("TTS generation completed.")
        self.generation_finished.emit(session)

    def _on_failed(self, message: str) -> None:
        self._running = False
        self.log_message.emit(f"TTS generation failed: {message}")
        self.generation_failed.emit(message)

    def _on_cancelled(self) -> None:
        self._running = False
        self.log_message.emit("TTS generation cancelled.")
        self.generation_cancelled.emit()

    def _on_thread_finished(self) -> None:
        self._running = False
        self.worker = None
        self.thread = None

    def cancel(self) -> None:
        if self._running and self.worker is not None:
            self.worker.request_cancel()

    def shutdown(self, *, wait: bool = True, timeout_ms: int = 5000) -> bool:
        worker, thread = self.worker, self.thread
        if worker is not None and self._running:
            worker.request_cancel()
        if thread is not None and thread.isRunning():
            thread.quit()
            if wait and not thread.wait(max(0, int(timeout_ms))):
                self.log_message.emit("TTS worker did not stop before shutdown timeout.")
                return False
        self._running = False
        self.worker = None
        self.thread = None
        return True

    def is_running(self) -> bool:
        return self._running

    def ready(self) -> bool:
        return not self._running

    def worker_instance(self):
        return self.worker

    def thread_instance(self):
        return self.thread

    def last_session(self):
        return self._last_session

    def output_file(self) -> str:
        return self._last_output

    def available_speakers(self) -> list[str]:
        if self.worker is None:
            return list(self._voice_profiles)
        self._voice_profiles = list(self.worker.available_speakers())
        return list(self._voice_profiles)

    def dispose(self) -> None:
        self.shutdown(wait=True)

    def __del__(self):
        try:
            self.shutdown(wait=False)
        except Exception:
            pass
