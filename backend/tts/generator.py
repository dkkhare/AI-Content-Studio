from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional

from backend.tts.adapters import (
    BaseTTSAdapter,
    GenerationRequest,
)

from backend.tts.progress import (
    TTSProgress,
)


class TTSGenerator:
    """
    High-level narration generator.

    Responsibilities
    ----------------
    • Split long text
    • Generate narration
    • Report progress
    • Track generation statistics
    • Cleanup temporary files
    """

    def __init__(
        self,
        adapter: BaseTTSAdapter,
        output_directory: str = "output/tts",
    ):

        self.adapter = adapter

        self.output_directory = Path(
            output_directory
        )

        self.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._generated_files: List[str] = []

        self._last_progress = None

        self._cancel_requested = False

        self._running = False

        self.chunk_size = 500
    # --------------------------------------------------
    # Reset
    # --------------------------------------------------

    def reset(
        self,
    ):

        self._generated_files.clear()

        self._last_progress = None

        self._cancel_requested = False

        self._running = False

    # --------------------------------------------------
    # Cancel
    # --------------------------------------------------

    def request_cancel(
        self,
    ):

        self._cancel_requested = True

    # --------------------------------------------------
    # Text Splitting
    # --------------------------------------------------

    def split_text(
        self,
        text: str,
    ) -> List[str]:

        text = (text or "").strip()

        if not text:

            return []

        if len(text) <= self.chunk_size:

            return [text]

        chunks = []

        current = ""

        for paragraph in text.split("\n"):

            paragraph = paragraph.strip()

            if not paragraph:

                continue

            if len(current) + len(paragraph) + 1 <= self.chunk_size:

                if current:

                    current += "\n"

                current += paragraph

            else:

                if current:

                    chunks.append(current)

                    current = ""

                while len(paragraph) > self.chunk_size:

                    chunks.append(
                        paragraph[: self.chunk_size]
                    )

                    paragraph = paragraph[
                        self.chunk_size :
                    ]

                current = paragraph

        if current:

            chunks.append(current)

        return chunks

    # --------------------------------------------------
    # Single Chunk
    # --------------------------------------------------

    def generate_chunk(
        self,
        reference_audio: str,
        reference_text: str,
        generation_text: str,
        output_file: str,
    ):

        if self._cancel_requested:

            raise RuntimeError(
                "Generation cancelled."
            )

        request = GenerationRequest(

            reference_audio=reference_audio,

            reference_text=reference_text,

            generation_text=generation_text,

            output_audio=output_file,

        )

        result = self.adapter.generate(
            request
        )

        self._generated_files.append(
            result.output_audio
        )

        return result
    # --------------------------------------------------
    # Multiple Chunks
    # --------------------------------------------------

    def generate(
        self,
        chunks: List[str],
        reference_audio: str,
        reference_text: str,
        progress_callback: Optional[
            Callable[[TTSProgress], None]
        ] = None,
    ) -> List[str]:

        self._running = True

        self._cancel_requested = False

        self._generated_files.clear()

        total = len(chunks)

        if total == 0:

            self._running = False

            return []

        try:

            for index, chunk in enumerate(chunks):

                if self._cancel_requested:

                    raise RuntimeError(
                        "Generation cancelled."
                    )

                output_file = (

                    self.output_directory

                    / f"chunk_{index + 1:04d}.wav"

                )

                result = self.generate_chunk(

                    reference_audio=reference_audio,

                    reference_text=reference_text,

                    generation_text=chunk,

                    output_file=str(output_file),

                )

                if result.output_audio not in self._generated_files:

                    self._generated_files.append(
                        result.output_audio
                    )

                progress = TTSProgress(

                    stage="Generating",

                    status="Running",

                    current_chunk=index + 1,

                    total_chunks=total,

                    current_text=chunk,

                )

                progress.update_percent()

                self._last_progress = progress

                if progress_callback:

                    progress_callback(
                        progress
                    )

            return list(
                self._generated_files
            )

        finally:

            self._running = False
    # --------------------------------------------------
    # Progress
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
    # Status
    # --------------------------------------------------

    def is_running(
        self,
    ):

        return self._running

    def is_finished(
        self,
    ):

        return not self._running

    def last_progress(
        self,
    ):

        return self._last_progress

    # --------------------------------------------------
    # Generated Files
    # --------------------------------------------------

    def generated_files(
        self,
    ):

        return list(
            self._generated_files
        )

    def generated_count(
        self,
    ):

        return len(
            self._generated_files
        )

    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------

    def statistics(
        self,
    ):

        return {

            "running": self._running,

            "cancel_requested": self._cancel_requested,

            "generated_files": len(
                self._generated_files
            ),

            "progress": self.progress_percent(),

            "output_directory": str(
                self.output_directory
            ),

        }
    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def clear_output(
        self,
    ):

        if not self.output_directory.exists():

            return

        for file in self.output_directory.glob(
            "*.wav"
        ):

            try:

                file.unlink()

            except Exception:

                pass

        self._generated_files.clear()

    # --------------------------------------------------

    def cleanup(
        self,
    ):

        self.request_cancel()

        try:

            if hasattr(
                self.adapter,
                "cleanup",
            ):

                self.adapter.cleanup()

        except Exception:

            pass

        self.reset()

    # --------------------------------------------------
    # Output Directory
    # --------------------------------------------------

    def output_path(
        self,
    ):

        return self.output_directory

    # --------------------------------------------------
    # Information
    # --------------------------------------------------

    def debug_info(
        self,
    ):

        return {

            "running": self._running,

            "cancel_requested": self._cancel_requested,

            "generated_files": len(
                self._generated_files
            ),

            "progress": self.progress_percent(),

            "output_directory": str(
                self.output_directory
            ),

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