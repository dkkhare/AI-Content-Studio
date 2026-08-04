from __future__ import annotations

from pathlib import Path
from typing import List

import numpy as np
import soundfile as sf


class AudioMerger:
    """
    Merge multiple generated audio chunks into a single WAV file.
    """

    def __init__(
        self,
        sample_rate: int = 24000,
        silence_ms: int = 150,
        normalize: bool = True,
    ):

        self.sample_rate = sample_rate
        self.silence_ms = silence_ms
        self.normalize = normalize

    # --------------------------------------------------
    # Silence
    # --------------------------------------------------

    def silence(self):

        samples = int(
            self.sample_rate *
            self.silence_ms /
            1000
        )

        return np.zeros(
            samples,
            dtype=np.float32,
        )

    # --------------------------------------------------
    # Normalize
    # --------------------------------------------------

    def normalize_audio(
        self,
        waveform,
    ):

        peak = np.max(
            np.abs(waveform)
        )

        if peak <= 0:

            return waveform

        return waveform * (
            0.98 / peak
        )

    # --------------------------------------------------
    # Merge
    # --------------------------------------------------

    def merge(
        self,
        input_files: List[str],
        output_file: str,
    ) -> str:

        if not input_files:

            raise ValueError(
                "No audio files supplied."
            )

        output_path = Path(output_file)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        merged = []

        silence = self.silence()

        for index, filename in enumerate(
            input_files
        ):

            audio, sr = sf.read(
                filename,
                dtype="float32",
            )

            if sr != self.sample_rate:

                raise ValueError(

                    f"Sample rate mismatch: "
                    f"{filename}"

                )

            if audio.ndim > 1:

                audio = np.mean(
                    audio,
                    axis=1,
                )

            merged.append(audio)

            if index != len(input_files) - 1:

                merged.append(
                    silence
                )

        merged_audio = np.concatenate(
            merged
        )

        if self.normalize:

            merged_audio = self.normalize_audio(
                merged_audio
            )

        sf.write(

            output_file,

            merged_audio,

            self.sample_rate,

        )

        return str(output_path)

    # --------------------------------------------------
    # Duration
    # --------------------------------------------------

    def duration(
        self,
        filename,
    ):

        info = sf.info(
            filename
        )

        return (
            info.frames /
            info.samplerate
        )

    # --------------------------------------------------
    # Total Duration
    # --------------------------------------------------

    def total_duration(
        self,
        files,
    ):

        total = 0.0

        for file in files:

            total += self.duration(
                file
            )

        if len(files) > 1:

            total += (

                (len(files) - 1)

                * self.silence_ms

                / 1000

            )

        return total

    # --------------------------------------------------
    # Verify
    # --------------------------------------------------

    def verify(
        self,
        files,
    ):

        if not files:

            return False

        for file in files:

            if not Path(file).exists():

                return False

        return True

    # --------------------------------------------------
    # Delete Chunks
    # --------------------------------------------------

    def cleanup(
        self,
        files,
    ):

        for file in files:

            try:

                Path(file).unlink()

            except Exception:

                pass