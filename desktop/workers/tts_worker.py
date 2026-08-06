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

    Lives inside a QThread and executes the
    backend TTSPipeline while forwarding
    progress updates to the UI.
    """

    # --------------------------------------------------
    # Signals
    # --------------------------------------------------

    started = Signal()

    progress = Signal(object)

    finished = Signal(object)

    failed = Signal(str)

    cancelled = Signal()

    log = Signal(str)

    # --------------------------------------------------

    def __init__(self, parent=None):

        super().__init__(parent)

        self.pipeline = TTSPipeline()

        self.session: Optional[TTSSession] = None

        self._cancel_requested = False

        self._running = False

        self.reference_audio: str = ""

        self.reference_text: str = ""

        self.text: str = ""

        self.output_directory: Optional[Path] = None

        self.voice_name: str = ""

        self.language: str = "en"

    # --------------------------------------------------
    # Properties
    # --------------------------------------------------

    @property
    def running(self) -> bool:

        return self._running

    @property
    def cancel_requested(self) -> bool:

        return self._cancel_requested
    # -----------------------------------------
    # Configure
    # -----------------------------------------

    def configure(
        self,
        reference_audio,
        reference_text,
        text,
        output_directory,
        voice_name: str = "",
        language: str = "en",
    ):

        self.reference_audio = str(
            reference_audio
        )

        self.reference_text = (
            reference_text or ""
        )

        self.text = text or ""

        self.output_directory = str(
            output_directory
        )

        self.voice_name = voice_name

        self.language = language

    # -----------------------------------------
    # Reset
    # -----------------------------------------

    def reset(self):

        self._cancel_requested = False

        self._running = False

        self.session = None

    # -----------------------------------------
    # Cancel
    # -----------------------------------------

    def request_cancel(self):

        if self._cancel_requested:
            return

        self.log.emit(
            "Cancellation requested..."
        )

        self._cancel_requested = True

        if (
            self.session is not None
            and hasattr(
                self.session,
                "cancel",
            )
        ):
            try:
                self.session.cancel()
            except Exception:
                pass
    # -----------------------------------------
    # Progress Callback
    # -----------------------------------------

    def progress_callback(
        self,
        progress: TTSProgress,
    ):

        if self._cancel_requested:

            raise RuntimeError(
                "TTS generation cancelled."
            )


        self.progress.emit(
            progress
        )


    # -----------------------------------------
    # Output Directory
    # -----------------------------------------

    def ensure_output_directory(
        self,
    ) -> Path:

        output = Path(
            self.output_directory
        )

        output.mkdir(
            parents=True,
            exist_ok=True,
        )

        return output


    # -----------------------------------------
    # Logging
    # -----------------------------------------

    def write_log(
        self,
        message: str,
    ):

        self.log.emit(
            message
        )


    # -----------------------------------------
    # Validation
    # -----------------------------------------

    def validate_inputs(
        self,
    ):

        if not self.text.strip():

            raise ValueError(
                "Input text is empty."
            )


        if not self.output_directory:

            raise ValueError(
                "Output directory not configured."
            )


        self.ensure_output_directory()
    # --------------------------------------------------
    # Worker Execution
    # --------------------------------------------------

    @Slot()
    def run(self):

        if self._running:

            return

        self._running = True

        self._cancel_requested = False

        self.started.emit()

        try:

            self.validate_inputs()

            self.write_log(
                "Starting TTS generation..."
            )

            self.session = self.pipeline.create_session(
                reference_audio=self.reference_audio,
                reference_text=self.reference_text,
                text=self.text,
                output_directory=self.output_directory,
                voice_name=self.voice_name,
                language=self.language,
            )

            result = self.pipeline.run(
                self.session,
                progress_callback=self.progress_callback,
            )

            if self._cancel_requested:

                self.write_log(
                    "TTS generation cancelled."
                )

                self.cancelled.emit()

                return

            self.write_log(
                "TTS generation completed."
            )

            self.finished.emit(
                result
            )

        except Exception as exc:

            self.write_log(
                f"TTS failed: {exc}"
            )

            self.failed.emit(
                str(exc)
            )

        finally:

            self._running = False