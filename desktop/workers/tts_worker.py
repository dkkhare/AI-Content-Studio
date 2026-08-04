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
    # --------------------------------------------------
    # Run
    # --------------------------------------------------

    @Slot()
    def run(self):
        """
        Execute narration generation.
        """

        self.reset()

        self._running = True

        self.started.emit()

        try:

            self.log.emit(
                "Initializing TTS pipeline..."
            )

            self.pipeline.initialize()

            self.ensure_output_directory()

            self.log.emit(
                "Creating session..."
            )

            self.session = self.pipeline.create_session(

                reference_audio=self.reference_audio,

                reference_text=self.reference_text,

                text=self.text,

            )

            self.log.emit(
                "Preparing text..."
            )

            chunks = self.create_chunks(
                self.text
            )

            if not chunks:

                raise RuntimeError(
                    "No text chunks generated."
                )

            self.log.emit(

                f"{len(chunks)} chunk(s) prepared."

            )

            self.session.total_chunks = len(
                chunks
            )

            self.log.emit(
                "Generating narration..."
            )

            self.pipeline.run(

                session=self.session,

                chunks=chunks,

                progress_callback=self.progress_callback,

            )

            if self._cancel_requested:

                self.session.cancel()

                self.cancelled.emit()

                return

            self.log.emit(
                "Generation completed."
            )

            self.finished.emit(
                self.session
            )

        except Exception as exc:

            if self.session:

                self.session.fail(
                    str(exc)
                )

            if self._cancel_requested:

                self.cancelled.emit()

            else:

                self.failed.emit(
                    str(exc)
                )

        finally:

            try:

                self.pipeline.shutdown()

            except Exception:

                pass

            self._running = False

    # --------------------------------------------------
    # Status
    # --------------------------------------------------

    def session_id(self):

        if self.session:

            return self.session.id

        return None

    def output_file(self):

        if self.session:

            return self.session.output_file

        return ""

    def progress_percent(self):

        if self.session:

            return self.session.progress

        return 0

    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def cleanup(self):

        if self.session:

            try:

                self.pipeline.cleanup_chunks(
                    self.session
                )

            except Exception:

                pass

    # --------------------------------------------------
    # Information
    # --------------------------------------------------

    def statistics(self):

        return self.pipeline.statistics()

    def is_finished(self):

        if self.session is None:

            return False

        return self.session.is_finished

    def is_running(self):

        return self._running

    # --------------------------------------------------
    # Reset
    # --------------------------------------------------

    def clear(self):

        self.cleanup()

        self.reset()

        self.reference_audio = ""

        self.reference_text = ""

        self.text = ""

        self.output_directory = ""