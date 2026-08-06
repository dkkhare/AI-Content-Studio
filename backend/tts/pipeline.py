from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional, List

from backend.tts.adapters import F5TTSAdapter
from backend.tts.audio_merger import AudioMerger
from backend.tts.generator import TTSGenerator
from backend.tts.progress import TTSProgress
from backend.tts.queue import TTSQueue
from backend.tts.session import TTSSession


class TTSPipeline:
    """
    End-to-end Text-to-Speech pipeline.

    Responsibilities
    ----------------
    • Session management
    • Queue management
    • Speech generation
    • Audio merging
    • Progress reporting
    • Voice profile management
    • Cleanup
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

        self.current_voice = ""

        self.current_language = "en"

        self.initialized = False

        self.initialize()
    # --------------------------------------------------
    # Session
    # --------------------------------------------------

    def create_session(
        self,
        reference_audio,
        reference_text,
        text,
        output_directory=None,
        voice_name="",
        language="en",
    ):

        if output_directory:

            self.output_directory = Path(
                output_directory
            )

            self.output_directory.mkdir(
                parents=True,
                exist_ok=True,
            )

            if hasattr(
                self.generator,
                "output_directory",
            ):

                self.generator.output_directory = (
                    self.output_directory
                )

        self.current_voice = (
            voice_name or ""
        )

        self.current_language = (
            language or "en"
        )

        session = TTSSession(

            reference_audio=reference_audio,

            reference_text=reference_text,

            input_text=text,

            output_directory=str(
                self.output_directory
            ),

        )

        # Optional fields for newer versions
        if hasattr(session, "voice_name"):

            session.voice_name = (
                self.current_voice
            )

        if hasattr(session, "language"):

            session.language = (
                self.current_language
            )

        self.queue.enqueue(
            session
        )

        return session

    # --------------------------------------------------
    # Run Session
    # --------------------------------------------------

    def run(
        self,
        session: TTSSession,
        chunks: Optional[List[str]] = None,
        progress_callback: Optional[
            Callable[[TTSProgress], None]
        ] = None,
    ):

        session.start()

        # --------------------------------------
        # Build chunks automatically if needed
        # --------------------------------------

        if chunks is None:

            if hasattr(
                self.generator,
                "split_text",
            ):

                chunks = self.generator.split_text(
                    session.input_text
                )

            else:

                chunks = [
                    session.input_text
                ]

        generated = self.generator.generate(

            chunks=chunks,

            reference_audio=session.reference_audio,

            reference_text=session.reference_text,

            progress_callback=progress_callback,

        )

        # --------------------------------------
        # Store generated chunks
        # --------------------------------------

        for wav in generated:

            session.add_chunk(
                wav
            )

        output_file = (
            self.output_directory
            / f"{session.id}.wav"
        )

        # --------------------------------------
        # Merge audio
        # --------------------------------------

        self.merger.merge(

            generated,

            str(output_file),

        )

        session.output_file = str(
            output_file
        )

        try:

            session.duration = (
                self.merger.duration(
                    output_file
                )
            )

        except Exception:

            session.duration = 0.0

        session.complete()

        self.queue.finish_current()

        return session
    # --------------------------------------------------
    # Voice Profiles
    # --------------------------------------------------

    def available_speakers(
        self,
    ):

        try:

            if hasattr(
                self.adapter,
                "available_speakers",
            ):

                return self.adapter.available_speakers()

        except Exception:

            pass

        return []



    def load_speaker(
        self,
        speaker_name: str,
    ):

        self.current_voice = speaker_name

        try:

            if hasattr(
                self.adapter,
                "load_speaker",
            ):

                self.adapter.load_speaker(
                    speaker_name
                )

        except Exception:

            pass



    # --------------------------------------------------
    # Queue Information
    # --------------------------------------------------

    def pending_sessions(
        self,
    ):

        return self.queue.pending()



    def running_sessions(
        self,
    ):

        return self.queue.running()



    def completed_sessions(
        self,
    ):

        return self.queue.completed()



    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def cleanup_chunks(
        self,
        session: TTSSession,
    ):

        try:

            self.merger.cleanup(
                session.generated_chunks
            )

        except Exception:

            pass



    def cleanup(
        self,
    ):

        try:

            if hasattr(
                self.generator,
                "cleanup",
            ):

                self.generator.cleanup()

        except Exception:

            pass

        try:

            if hasattr(
                self.merger,
                "cleanup_all",
            ):

                self.merger.cleanup_all()

        except Exception:

            pass
    # --------------------------------------------------
    # Adapter Lifecycle
    # --------------------------------------------------

    def initialize(
        self,
    ):

        if self.initialized:

            return

        try:

            self.adapter.initialize()

        finally:

            self.initialized = True



    def shutdown(
        self,
    ):

        try:

            self.adapter.shutdown()

        except Exception:

            pass

        self.initialized = False



    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------

    def statistics(
        self,
    ):

        stats = {

            "initialized": self.initialized,

            "voice": self.current_voice,

            "language": self.current_language,

            "queued": self.queue.size(),

            "completed": len(
                self.queue.completed()
            ),

            "failed": len(
                self.queue.failed()
            ),

            "history": len(
                self.queue.history()
            ),

        }

        try:

            if hasattr(
                self.adapter,
                "statistics",
            ):

                adapter_stats = (
                    self.adapter.statistics()
                )

                if isinstance(
                    adapter_stats,
                    dict,
                ):

                    stats.update(
                        adapter_stats
                    )

        except Exception:

            pass

        return stats



    # --------------------------------------------------
    # Debug
    # --------------------------------------------------

    def debug_info(
        self,
    ):

        return {

            "output_directory": str(
                self.output_directory
            ),

            "voice": self.current_voice,

            "language": self.current_language,

            "initialized": self.initialized,

            "queue_size": self.queue.size(),

        }



    # --------------------------------------------------
    # Destructor
    # --------------------------------------------------

    def __del__(
        self,
    ):

        try:

            self.shutdown()

        except Exception:

            pass