from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional

from backend.tts.adapters import BaseTTSAdapter, F5TTSAdapter
from backend.tts.audio_merger import AudioMerger
from backend.tts.generator import TTSGenerator
from backend.tts.progress import TTSProgress
from backend.tts.queue import TTSQueue
from backend.tts.session import TTSSession


class TTSPipeline:
    """End-to-end narration pipeline with explicit session lifecycle handling."""

    def __init__(
        self,
        output_directory: str = "output/tts",
        *,
        adapter: BaseTTSAdapter | None = None,
        merger: AudioMerger | None = None,
    ):
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)
        self.adapter = adapter or F5TTSAdapter()
        self.generator = TTSGenerator(self.adapter, self.output_directory)
        self.merger = merger or AudioMerger()
        self.queue = TTSQueue()
        self.current_voice = ""
        self.current_language = "en"
        self.initialized = False
        self.initialize()

    def create_session(
        self,
        reference_audio,
        reference_text,
        text,
        output_directory=None,
        voice_name="",
        language="en",
    ) -> TTSSession:
        if output_directory:
            self.output_directory = Path(output_directory)
            self.output_directory.mkdir(parents=True, exist_ok=True)
            self.generator.output_directory = self.output_directory

        session = TTSSession(
            reference_audio=str(reference_audio),
            reference_text=str(reference_text or ""),
            input_text=str(text or ""),
            output_directory=str(self.output_directory),
            voice_name=str(voice_name or ""),
            language=str(language or "en"),
        )
        self.current_voice = session.voice_name
        self.current_language = session.language
        return self.queue.enqueue(session)

    def _activate(self, session: TTSSession) -> None:
        current = self.queue.current()
        if current is session:
            return
        activated = self.queue.dequeue()
        if activated is not session:
            raise RuntimeError("TTS sessions must run in queue order.")

    def run(
        self,
        session: TTSSession,
        chunks: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[TTSProgress], None]] = None,
    ) -> TTSSession:
        self._activate(session)
        session.start()
        generated: list[str] = []

        if chunks is None:
            chunks = self.generator.split_text(session.input_text)
        if not chunks:
            error = ValueError("Narration text produced no generation chunks.")
            session.fail(str(error))
            self.queue.finish_current()
            raise error

        session.total_chunks = len(chunks)

        def report(progress: TTSProgress) -> None:
            session.update_progress(progress.current_chunk, progress.total_chunks)
            if progress_callback:
                progress_callback(progress)

        try:
            generated = self.generator.generate(
                chunks=chunks,
                reference_audio=session.reference_audio,
                reference_text=session.reference_text,
                progress_callback=report,
            )
            for filename in generated:
                session.add_chunk(filename)

            output_file = self.output_directory / f"{session.id}.wav"
            self.merger.merge(generated, str(output_file))
            session.output_file = str(output_file)
            session.duration = self.merger.duration(output_file)
            session.complete()
            return session
        except Exception as exc:
            cancelled = session.cancelled or "cancel" in str(exc).lower()
            if cancelled:
                session.cancel()
            else:
                session.fail(str(exc))
            partial = list(dict.fromkeys(generated + self.generator.generated_files()))
            self.merger.cleanup(partial)
            raise
        finally:
            self.queue.finish_current()

    def request_cancel(self) -> None:
        current = self.queue.current()
        if current is not None:
            current.cancel()
        self.generator.request_cancel()

    def available_speakers(self):
        try:
            return list(self.adapter.available_speakers())
        except (AttributeError, RuntimeError):
            return []

    def load_speaker(self, speaker_name: str):
        self.current_voice = speaker_name
        if hasattr(self.adapter, "load_speaker"):
            self.adapter.load_speaker(speaker_name)

    def pending_sessions(self):
        return self.queue.pending()

    def running_sessions(self):
        return self.queue.running()

    def completed_sessions(self):
        return self.queue.completed()

    def cleanup_chunks(self, session: TTSSession):
        self.merger.cleanup(session.generated_chunks)

    def cleanup(self):
        self.generator.cleanup()

    def initialize(self):
        if not self.initialized:
            self.adapter.initialize()
            self.initialized = True

    def shutdown(self):
        if self.initialized:
            try:
                self.adapter.shutdown()
            finally:
                self.initialized = False

    def statistics(self):
        stats = {
            "initialized": self.initialized,
            "voice": self.current_voice,
            "language": self.current_language,
            "queued": self.queue.size(),
            "completed": len(self.queue.completed()),
            "failed": len(self.queue.failed()),
            "history": len(self.queue.history()),
        }
        if hasattr(self.adapter, "statistics"):
            stats.update(self.adapter.statistics())
        return stats

    def debug_info(self):
        return {
            "output_directory": str(self.output_directory),
            "voice": self.current_voice,
            "language": self.current_language,
            "initialized": self.initialized,
            "queue_size": self.queue.size(),
        }

    def __del__(self):
        try:
            self.shutdown()
        except Exception:
            pass
