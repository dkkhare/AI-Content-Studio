from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import (
    QObject,
    QThread,
    Signal,
)

from desktop.workers.tts_worker import TTSWorker


class TTSController(QObject):
    """
    Controls background TTS generation.

    Creates the worker thread, forwards progress
    to the UI and manages the worker lifecycle.
    """

    # --------------------------------------------------
    # Signals
    # --------------------------------------------------

    generation_started = Signal()

    generation_progress = Signal(object)

    generation_finished = Signal(object)

    generation_failed = Signal(str)

    generation_cancelled = Signal()

    log_message = Signal(str)

    # --------------------------------------------------

    def __init__(self, parent=None):

        super().__init__(parent)

        self.thread: Optional[QThread] = None

        self.worker: Optional[TTSWorker] = None

        self._running = False

        self._last_session = None

        self._last_output = ""

    # --------------------------------------------------
    # Thread creation
    # --------------------------------------------------

    def _create_worker(self):

        self.thread = QThread()

        self.worker = TTSWorker()

        self.worker.moveToThread(
            self.thread
        )

        # ---------- Thread ----------

        self.thread.started.connect(
            self.worker.run
        )

        # ---------- Worker ----------

        self.worker.started.connect(
            self._on_started
        )

        self.worker.progress.connect(
            self._on_progress
        )

        self.worker.finished.connect(
            self._on_finished
        )

        self.worker.failed.connect(
            self._on_failed
        )

        self.worker.cancelled.connect(
            self._on_cancelled
        )

        self.worker.log.connect(
            self.log_message.emit
        )

        # ---------- Cleanup ----------

        self.worker.finished.connect(
            self.thread.quit
        )

        self.worker.failed.connect(
            self.thread.quit
        )

        self.worker.cancelled.connect(
            self.thread.quit
        )

        self.thread.finished.connect(
            self.thread.deleteLater
        )

        self.thread.finished.connect(
            self.worker.deleteLater
        )
    # --------------------------------------------------
    # Start Generation
    # --------------------------------------------------

    def generate(

        self,

        reference_audio: str,

        reference_text: str,

        text: str,

        output_directory: str,

    ):

        if self._running:

            raise RuntimeError(

                "A narration job is already running."

            )

        if not text.strip():

            raise ValueError(

                "Text cannot be empty."

            )

        output_directory = str(

            Path(output_directory)

        )

        Path(output_directory).mkdir(

            parents=True,

            exist_ok=True,

        )

        self._last_session = None

        self._last_output = ""

        self._create_worker()

        self.worker.configure(

            reference_audio=reference_audio,

            reference_text=reference_text,

            text=text,

            output_directory=output_directory,

        )

        self._running = True

        self.thread.start()

    # --------------------------------------------------
    # Status
    # --------------------------------------------------

    def is_running(self):

        return self._running

    def ready(self):

        return not self._running

    def worker_instance(self):

        return self.worker

    def thread_instance(self):

        return self.thread

    # --------------------------------------------------
    # Cancel
    # --------------------------------------------------

    def cancel(self):

        if not self._running:

            return

        if self.worker:

            self.worker.request_cancel()
    # --------------------------------------------------
    # Worker Slots
    # --------------------------------------------------

    def _on_started(self):

        self.log_message.emit(
            "TTS generation started."
        )

        self.generation_started.emit()

    def _on_progress(
        self,
        progress,
    ):

        self.generation_progress.emit(
            progress
        )

    def _on_finished(
        self,
        session,
    ):

        self._running = False

        self._last_session = session

        try:

            if session is not None:

                self._last_output = getattr(
                    session,
                    "output_file",
                    "",
                )

        except Exception:

            self._last_output = ""

        self.log_message.emit(
            "TTS generation completed."
        )

        self.generation_finished.emit(
            session
        )

    def _on_failed(
        self,
        message,
    ):

        self._running = False

        self.log_message.emit(
            f"TTS generation failed: {message}"
        )

        self.generation_failed.emit(
            message
        )

    def _on_cancelled(self):

        self._running = False

        self.log_message.emit(
            "TTS generation cancelled."
        )

        self.generation_cancelled.emit()
    # --------------------------------------------------
    # Session Information
    # --------------------------------------------------

    def session(self):

        if self.worker:

            return self.worker.session

        return self._last_session

    def session_id(self):

        session = self.session()

        if session and hasattr(session, "id"):

            return session.id

        if self.worker:

            try:

                return self.worker.session_id()

            except Exception:

                pass

        return None

    def output_file(self):

        if self._last_output:

            return self._last_output

        if self.worker:

            try:

                return self.worker.output_file()

            except Exception:

                pass

        return ""

    def progress_percent(self):

        if self.worker:

            try:

                return self.worker.progress_percent()

            except Exception:

                pass

        return 0

    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------

    def statistics(self):

        if self.worker:

            try:

                return self.worker.statistics()

            except Exception:

                pass

        return {}

    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def cleanup(self):

        if self.worker:

            try:

                self.worker.cleanup()

            except Exception:

                pass

    def reset(self):

        self.cleanup()

        self.worker = None

        self.thread = None

        self._running = False

    # --------------------------------------------------
    # Wait
    # --------------------------------------------------

    def wait(self, timeout=30000):

        if self.thread:

            return self.thread.wait(timeout)

        return True

    # --------------------------------------------------
    # Convenience
    # --------------------------------------------------

    def is_finished(self):

        if self.worker:

            try:

                return self.worker.is_finished()

            except Exception:

                pass

        return not self._running

    def has_session(self):

        return self.session() is not None

    # --------------------------------------------------
    # Output
    # --------------------------------------------------

    def output_exists(self):

        output = self.output_file()

        if not output:

            return False

        return Path(output).exists()

    def output_duration(self):

        session = self.session()

        if session and hasattr(session, "duration"):

            return session.duration

        return 0.0

    # --------------------------------------------------
    # Destructor
    # --------------------------------------------------

    def shutdown(self):

        if self._running:

            self.cancel()

            self.wait()

        self.reset()