from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from backend.tts.adapters import F5TTSAdapter
from backend.tts.audio_merger import AudioMerger
from backend.tts.generator import TTSGenerator
from backend.tts.progress import TTSProgress
from backend.tts.queue import TTSQueue
from backend.tts.session import TTSSession


class TTSPipeline:
    """
    End-to-end TTS generation pipeline.

    Responsibilities
    ----------------
    • Manage sessions
    • Generate speech
    • Merge audio
    • Update progress
    • Manage queue
    """

    def __init__(
        self,
        output_directory="output/tts",
    ):

        self.output_directory = Path(
            output_directory
        )

        self.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.adapter = F5TTSAdapter()

        self.generator = TTSGenerator(

            adapter=self.adapter,

            output_directory=self.output_directory,

        )

        self.merger = AudioMerger()

        self.queue = TTSQueue()

    # --------------------------------------------------
    # Session
    # --------------------------------------------------

    def create_session(

        self,

        reference_audio,

        reference_text,

        text,

    ):

        session = TTSSession(

            reference_audio=reference_audio,

            reference_text=reference_text,

            input_text=text,

            output_directory=str(
                self.output_directory
            ),

        )

        self.queue.enqueue(session)

        return session

    # --------------------------------------------------
    # Run Session
    # --------------------------------------------------

    def run(

        self,

        session: TTSSession,

        chunks,

        progress_callback: Optional[
            Callable[[TTSProgress], None]
        ] = None,

    ):

        session.start()

        generated = self.generator.generate(

            chunks=chunks,

            reference_audio=session.reference_audio,

            reference_text=session.reference_text,

            progress_callback=progress_callback,

        )

        for wav in generated:

            session.add_chunk(wav)

        output_file = (

            self.output_directory

            / f"{session.id}.wav"

        )

        self.merger.merge(

            generated,

            str(output_file),

        )

        session.output_file = str(
            output_file
        )

        session.duration = self.merger.duration(
            output_file
        )

        session.complete()

        self.queue.finish_current()

        return session

    # --------------------------------------------------
    # Process Queue
    # --------------------------------------------------

    def process_queue(

        self,

        chunk_provider,

        progress_callback=None,

    ):

        while not self.queue.is_empty():

            session = self.queue.dequeue()

            if session is None:

                break

            chunks = chunk_provider(

                session.input_text

            )

            self.run(

                session,

                chunks,

                progress_callback,

            )

    # --------------------------------------------------
    # Cancel
    # --------------------------------------------------

    def cancel(

        self,

        session_id,

    ):

        session = self.queue.find(
            session_id
        )

        if session:

            session.cancel()

            return True

        return False

    # --------------------------------------------------
    # Queue
    # --------------------------------------------------

    def pending_sessions(self):

        return self.queue.pending()

    def running_sessions(self):

        return self.queue.running()

    def completed_sessions(self):

        return self.queue.completed()

    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def cleanup_chunks(

        self,

        session: TTSSession,

    ):

        self.merger.cleanup(

            session.generated_chunks

        )

    # --------------------------------------------------
    # Adapter
    # --------------------------------------------------

    def initialize(self):

        self.adapter.initialize()

    def shutdown(self):

        self.adapter.shutdown()

    # --------------------------------------------------
    # Information
    # --------------------------------------------------

    def statistics(self):

        return {

            "queued": self.queue.size(),

            "completed":

                len(

                    self.queue.completed()

                ),

            "failed":

                len(

                    self.queue.failed()

                ),

            "history":

                len(

                    self.queue.history()

                ),

        }