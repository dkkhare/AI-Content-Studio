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
    Background worker for AI narration generation.

    Responsibilities
    ----------------
    • Execute TTSPipeline in a background thread
    • Report progress
    • Support cancellation
    • Maintain generation session
    • Expose statistics and output information
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
    # Constructor
    # --------------------------------------------------

    def __init__(self, parent=None):

        super().__init__(parent)

        self.pipeline = TTSPipeline()

        self.session: Optional[TTSSession] = None

        self._cancel_requested = False

        self._running = False

        self._last_progress = None

        self._last_output = ""

        self.reference_audio = ""

        self.reference_text = ""

        self.text = ""

        self.output_directory = ""

        self.voice_name = ""

        self.language = "en"

    # --------------------------------------------------
    # Properties
    # --------------------------------------------------

    @property
    def running(self):

        return self._running

    @property
    def cancel_requested(self):

        return self._cancel_requested

    # --------------------------------------------------
    # Configure
    # --------------------------------------------------

    def configure(
        self,
        reference_audio,
        reference_text,
        text,
        output_directory,
        voice_name="",
        language="en",
    ):

        self.reference_audio = str(reference_audio)

        self.reference_text = reference_text or ""

        self.text = text or ""

        self.output_directory = str(output_directory)

        self.voice_name = voice_name

        self.language = language

    # --------------------------------------------------
    # Reset
    # --------------------------------------------------

    def reset(self):

        self._cancel_requested = False

        self._running = False

        self._last_progress = None

        self._last_output = ""

        self.session = None

    # --------------------------------------------------
    # Cancel
    # --------------------------------------------------

    def request_cancel(self):

        if self._cancel_requested:

            return

        self._cancel_requested = True

        self.log.emit(
            "Cancellation requested..."
        )

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
    # --------------------------------------------------
    # Progress Callback
    # --------------------------------------------------

    def progress_callback(
        self,
        progress: TTSProgress,
    ):

        if self._cancel_requested:

            raise RuntimeError(
                "TTS generation cancelled."
            )

        self._last_progress = progress

        self.progress.emit(
            progress
        )

    # --------------------------------------------------
    # Output Directory
    # --------------------------------------------------

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

    # --------------------------------------------------
    # Logging
    # --------------------------------------------------

    def write_log(
        self,
        message: str,
    ):

        self.log.emit(
            message
        )

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------

    def validate_inputs(
        self,
    ):

        if not self.reference_audio:

            raise ValueError(
                "Reference audio is required."
            )

        if not Path(
            self.reference_audio
        ).exists():

            raise FileNotFoundError(
                "Reference audio file not found."
            )

        if not self.reference_text.strip():

            raise ValueError(
                "Reference transcript is empty."
            )

        if not self.text.strip():

            raise ValueError(
                "Narration text is empty."
            )

        if not self.output_directory:

            raise ValueError(
                "Output directory is not configured."
            )

        self.ensure_output_directory()

    # --------------------------------------------------
    # Voice Profiles
    # --------------------------------------------------

    def available_speakers(
        self,
    ):

        try:

            if hasattr(
                self.pipeline,
                "available_speakers",
            ):

                return self.pipeline.available_speakers()

        except Exception:

            pass

        return []

    def load_speaker(
        self,
        speaker_name: str,
    ):

        self.voice_name = speaker_name

        try:

            if hasattr(
                self.pipeline,
                "load_speaker",
            ):

                self.pipeline.load_speaker(
                    speaker_name
                )

        except Exception as exc:

            self.log.emit(
                f"Unable to load speaker: {exc}"
            )
    # --------------------------------------------------
    # Worker Execution
    # --------------------------------------------------

    @Slot()
    def run(
        self,
    ):

        if self._running:

            return


        self._running = True

        self._cancel_requested = False

        self._last_output = ""

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
                    "Generation cancelled."
                )

                self.cancelled.emit()

                return


            self._last_output = getattr(

                result,

                "output_file",

                "",

            )


            self.write_log(
                "Narration generation completed."
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
    # --------------------------------------------------
    # Session Helpers
    # --------------------------------------------------

    def session_id(
        self,
    ):

        if (
            self.session is not None
            and hasattr(
                self.session,
                "id",
            )
        ):

            return self.session.id

        return None

    # --------------------------------------------------

    def output_file(
        self,
    ):

        if self._last_output:

            return self._last_output

        if (
            self.session is not None
            and hasattr(
                self.session,
                "output_file",
            )
        ):

            return self.session.output_file

        return ""

    # --------------------------------------------------

    def progress_percent(
        self,
    ):

        progress = self._last_progress

        if progress is None:

            return 0

        for attr in (
            "percent",
            "percentage",
            "progress",
            "value",
        ):

            if hasattr(
                progress,
                attr,
            ):

                try:

                    return int(
                        getattr(
                            progress,
                            attr,
                        )
                    )

                except Exception:

                    pass

        return 0

    # --------------------------------------------------

    def statistics(
        self,
    ):

        stats = {

            "running": self._running,

            "cancel_requested": self._cancel_requested,

            "output_file": self.output_file(),

            "progress": self.progress_percent(),

            "voice": self.voice_name,

            "language": self.language,

        }

        if (
            self.session is not None
            and hasattr(
                self.session,
                "statistics",
            )
        ):

            try:

                extra = self.session.statistics()

                if isinstance(
                    extra,
                    dict,
                ):

                    stats.update(extra)

            except Exception:

                pass

        return stats

    # --------------------------------------------------

    def is_finished(
        self,
    ):

        return (
            not self._running
        )
    # --------------------------------------------------
    # Output Helpers
    # --------------------------------------------------

    def output_exists(
        self,
    ):

        output = self.output_file()

        if not output:

            return False

        return Path(output).exists()

    # --------------------------------------------------

    def output_duration(
        self,
    ):

        if (
            self.session is not None
            and hasattr(
                self.session,
                "duration",
            )
        ):

            try:

                return float(
                    self.session.duration
                )

            except Exception:

                pass

        return 0.0

    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def cleanup(
        self,
    ):

        try:

            if (
                self.pipeline is not None
                and hasattr(
                    self.pipeline,
                    "cleanup",
                )
            ):

                self.pipeline.cleanup()

        except Exception:

            pass

        self._cancel_requested = False

        self._running = False

        self._last_progress = None

        self._last_output = ""

    # --------------------------------------------------

    def reset_worker(
        self,
    ):

        self.cleanup()

        self.session = None

    # --------------------------------------------------
    # Debug
    # --------------------------------------------------

    def debug_info(
        self,
    ):

        return {

            "running": self._running,

            "cancel_requested": self._cancel_requested,

            "session": self.session is not None,

            "output_file": self.output_file(),

            "progress": self.progress_percent(),

            "voice": self.voice_name,

            "language": self.language,

        }

    # --------------------------------------------------
    # Destructor
    # --------------------------------------------------

    def __del__(
        self,
    ):

        try:

            self.cleanup()

        except Exception:

            pass