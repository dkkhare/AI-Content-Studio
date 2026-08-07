from __future__ import annotations

from pathlib import Path
from typing import List

import numpy as np
import soundfile as sf


class AudioMerger:
    """
    Merge generated audio chunks into a single WAV file.

    Features
    --------
    • Merge multiple WAV files
    • Optional silence between chunks
    • Peak normalization
    • Duration calculation
    • Chunk cleanup
    • Audio verification
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

        self._last_output = None
    # --------------------------------------------------
    # Silence
    # --------------------------------------------------

    def silence(
        self,
    ) -> np.ndarray:

        samples = int(

            self.sample_rate
            * self.silence_ms
            / 1000

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
        waveform: np.ndarray,
    ) -> np.ndarray:

        if waveform.size == 0:

            return waveform

        peak = np.max(

            np.abs(waveform)

        )

        if peak <= 0:

            return waveform

        return waveform * (

            0.98 / peak

        )

    # --------------------------------------------------
    # Load Audio
    # --------------------------------------------------

    def load_audio(
        self,
        filename: str,
    ) -> np.ndarray:

        path = Path(filename)

        if not path.exists():

            raise FileNotFoundError(

                str(path)

            )

        audio, sr = sf.read(

            path,

            dtype="float32",

        )

        if sr != self.sample_rate:

            raise ValueError(

                f"Sample rate mismatch: {path}"

            )

        if audio.ndim > 1:

            audio = np.mean(

                audio,

                axis=1,

            )

        return audio

    # --------------------------------------------------
    # Save Audio
    # --------------------------------------------------

    def save_audio(
        self,
        waveform: np.ndarray,
        filename: str,
    ) -> str:

        output = Path(filename)

        output.parent.mkdir(

            parents=True,

            exist_ok=True,

        )

        sf.write(

            output,

            waveform,

            self.sample_rate,

        )

        self._last_output = str(output)

        return str(output)
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

        merged_audio = []

        silence = self.silence()

        total = len(input_files)

        for index, filename in enumerate(
            input_files
        ):

            audio = self.load_audio(
                filename
            )

            merged_audio.append(
                audio
            )

            if index < total - 1:

                merged_audio.append(
                    silence
                )

        if not merged_audio:

            raise RuntimeError(
                "Nothing to merge."
            )

        final_audio = np.concatenate(
            merged_audio
        )

        if self.normalize:

            final_audio = self.normalize_audio(
                final_audio
            )

        output = self.save_audio(

            final_audio,

            output_file,

        )

        return output
    # --------------------------------------------------
    # Duration
    # --------------------------------------------------

    def duration(
        self,
        filename: str,
    ) -> float:

        path = Path(filename)

        if not path.exists():

            return 0.0

        try:

            info = sf.info(path)

            return (

                info.frames
                / info.samplerate

            )

        except Exception:

            return 0.0

    # --------------------------------------------------
    # Total Duration
    # --------------------------------------------------

    def total_duration(
        self,
        files: List[str],
    ) -> float:

        total = 0.0

        for filename in files:

            total += self.duration(
                filename
            )

        if len(files) > 1:

            total += (

                (len(files) - 1)
                * self.silence_ms
                / 1000.0

            )

        return total

    # --------------------------------------------------
    # Verify
    # --------------------------------------------------

    def verify(
        self,
        files: List[str],
    ) -> bool:

        if not files:

            return False

        for filename in files:

            path = Path(filename)

            if not path.exists():

                return False

            try:

                info = sf.info(path)

                if info.frames == 0:

                    return False

                if info.samplerate != self.sample_rate:

                    return False

            except Exception:

                return False

        return True

    # --------------------------------------------------
    # Last Output
    # --------------------------------------------------

    def last_output(
        self,
    ) -> str | None:

        return self._last_output
    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def cleanup(
        self,
        files: List[str],
    ):

        for filename in files:

            try:

                path = Path(filename)

                if path.exists():

                    path.unlink()

            except Exception:

                pass

    # --------------------------------------------------
    # Cleanup Directory
    # --------------------------------------------------

    def cleanup_directory(
        self,
    ):

        if not self.output_directory.exists():

            return

        for wav in self.output_directory.glob("*.wav"):

            try:

                wav.unlink()

            except Exception:

                pass

    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------

    def statistics(
        self,
    ):

        files = list(
            self.output_directory.glob("*.wav")
        )

        return {

            "sample_rate": self.sample_rate,

            "silence_ms": self.silence_ms,

            "normalize": self.normalize,

            "generated_files": len(files),

            "last_output": self._last_output,

        }

    # --------------------------------------------------
    # Reset
    # --------------------------------------------------

    def reset(
        self,
    ):

        self._last_output = None

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

            "sample_rate": self.sample_rate,

            "silence_ms": self.silence_ms,

            "normalize": self.normalize,

            "last_output": self._last_output,

        }