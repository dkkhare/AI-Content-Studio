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

    Creates the worker thread, forwards progress to the UI,
    and exposes a simple API for starting and stopping
    narration generation.
    """

    # --------------------------------------------------
    # Signals forwarded to UI
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

    # --------------------------------------------------
    # Thread creation
    # --------------------------------------------------

    def _create_worker(self):

        self.thread = QThread()

        self.worker = TTSWorker()

        self.worker.moveToThread(self.thread)

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
    # Start generation
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

        output_directory = str(

            Path(output_directory)

        )

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

    def worker_instance(self):

        return self.worker

    def thread_instance(self):

        return self.thread