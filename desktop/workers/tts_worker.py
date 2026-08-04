from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import (
    QObject,
    Signal,
    Slot,
)

from backend.tts.pipeline import TTSPipeline
from backend.tts.progress import TTSProgress
from backend.tts.session import TTSSession


class TTSWorker(QObject):
    """
    Background worker for narration generation.

    This object lives inside a QThread.

    Responsibilities

    • Run the TTSPipeline
    • Emit progress updates
    • Support cancellation
    • Report completion
    • Report errors
    """

    # -----------------------------------------
    # Signals
    # -----------------------------------------

    started = Signal()

    progress = Signal(object)

    finished = Signal(object)

    failed = Signal(str)

    cancelled = Signal()

    log = Signal(str)

    # -----------------------------------------

    def __init__(self):

        super().__init__()

        self.pipeline = TTSPipeline()

        self.session: Optional[TTSSession] = None

        self._cancel_requested = False

        self._running = False

        self.reference_audio = ""

        self.reference_text = ""

        self.text = ""

        self.output_directory = ""

    # -----------------------------------------
    # Configure
    # -----------------------------------------

    def configure(

        self,

        reference_audio,

        reference_text,

        text,

        output_directory,

    ):

        self.reference_audio = reference_audio

        self.reference_text = reference_text

        self.text = text

        self.output_directory = output_directory

    # -----------------------------------------

    @property
    def running(self):

        return self._running

    # -----------------------------------------

    @property
    def cancel_requested(self):

        return self._cancel_requested

    # -----------------------------------------

    def reset(self):

        self._cancel_requested = False

        self._running = False

        self.session = None

    # -----------------------------------------

    def request_cancel(self):

        self.log.emit(

            "Cancellation requested."

        )

        self._cancel_requested = True

    # -----------------------------------------
    # Progress callback
    # -----------------------------------------

    def progress_callback(

        self,

        progress: TTSProgress,

    ):

        if self._cancel_requested:

            raise RuntimeError(

                "Generation cancelled."

            )

        self.progress.emit(progress)

    # -----------------------------------------
    # Utilities
    # -----------------------------------------

    def create_chunks(

        self,

        text,

    ):

        manager = self.pipeline.generator

        if hasattr(

            manager,

            "create_chunks",

        ):

            return manager.create_chunks(text)

        return [

            text

        ]

    # -----------------------------------------

    def ensure_output_directory(self):

        path = Path(

            self.output_directory

        )

        path.mkdir(

            parents=True,

            exist_ok=True,

        )

        return path