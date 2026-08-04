from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional

from backend.tts.adapters import (
    BaseTTSAdapter,
    GenerationRequest,
)
from backend.tts.progress import TTSProgress


class TTSGenerator:
    """
    High-level narration generator.

    Responsibilities
    ----------------
    • Generate speech from long text
    • Process one chunk at a time
    • Report progress
    • Return generated audio files
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

        request = GenerationRequest(

            reference_audio=reference_audio,

            reference_text=reference_text,

            generation_text=generation_text,

            output_audio=output_file,

        )

        result = self.adapter.generate(
            request
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

        generated_files = []

        total = len(chunks)

        for index, chunk in enumerate(chunks):

            output_file = (

                self.output_directory

                / f"chunk_{index+1:04d}.wav"

            )

            result = self.generate_chunk(

                reference_audio=reference_audio,

                reference_text=reference_text,

                generation_text=chunk,

                output_file=str(output_file),

            )

            generated_files.append(
                result.output_audio
            )

            if progress_callback:

                progress = TTSProgress(

                    stage="Generating",

                    status="Running",

                    current_chunk=index + 1,

                    total_chunks=total,

                    current_text=chunk,

                )

                progress.update_percent()

                progress_callback(progress)

        return generated_files

    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def clear_output(self):

        if not self.output_directory.exists():

            return

        for file in self.output_directory.glob(
            "*.wav"
        ):

            try:

                file.unlink()

            except Exception:

                pass

    # --------------------------------------------------
    # Output Directory
    # --------------------------------------------------

    def output_path(self):

        return self.output_directory

    # --------------------------------------------------
    # Count
    # --------------------------------------------------

    def generated_count(self):

        return len(

            list(

                self.output_directory.glob(
                    "*.wav"
                )

            )

        )