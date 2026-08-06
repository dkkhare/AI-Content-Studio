
from __future__ import annotations

from pathlib import Path
from typing import Optional


from PySide6.QtCore import (
    QObject,
    QThread,
    Signal,
)


from desktop.workers.tts_worker import (
    TTSWorker,
)



class TTSController(QObject):

    """
    Controls background TTS generation.

    Responsibilities:

    - Create worker thread
    - Forward worker signals
    - Manage lifecycle
    - Manage sessions
    - Provide UI helpers
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

    def __init__(
        self,
        parent=None,
    ):

        super().__init__(
            parent
        )


        self.thread: Optional[QThread] = None

        self.worker: Optional[TTSWorker] = None


        self._running = False


        self._last_session = None

        self._last_output = ""


        self._voice_profiles = []

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


        if not reference_audio:

            raise ValueError(
                "Reference audio is required."
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

    def is_running(
        self,
    ):

        return self._running



    def ready(
        self,
    ):

        return not self._running



    def worker_instance(
        self,
    ):

        return self.worker



    def thread_instance(
        self,
    ):

        return self.thread



    # --------------------------------------------------
    # Cancel
    # --------------------------------------------------

    def cancel(
        self,
    ):

        if not self._running:

            return


        if self.worker:

            try:

                self.worker.request_cancel()


            except Exception as exc:

                self.log_message.emit(

                    f"Cancel error: {exc}"

                )



    # --------------------------------------------------
    # Worker Event Handlers
    # --------------------------------------------------

    def _on_started(
        self,
    ):

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


        self._last_output = ""


        if session:

            self._last_output = getattr(

                session,

                "output_file",

                "",

            )


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



    def _on_cancelled(
        self,
    ):

        self._running = False


        self.log_message.emit(

            "TTS generation cancelled."

        )


        self.generation_cancelled.emit()
desktop/controllers/tts_controller.py