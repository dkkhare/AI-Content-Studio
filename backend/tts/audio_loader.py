from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

from backend.tts.audio_info import AudioInfo


class AudioLoader:
    """
    Loads audio files and converts them into a mono waveform.
    """

    SUPPORTED_FORMATS = {
        ".wav",
        ".mp3",
        ".flac",
        ".ogg",
        ".m4a",
    }

    def load(
        self,
        filename: str,
        target_sample_rate: int | None = None,
    ):

        path = Path(filename)

        if not path.exists():

            raise FileNotFoundError(filename)

        if path.suffix.lower() not in self.SUPPORTED_FORMATS:

            raise ValueError(
                f"Unsupported format: {path.suffix}"
            )

        waveform, sample_rate = librosa.load(
            filename,
            sr=target_sample_rate,
            mono=True,
        )

        info = sf.info(filename)

        audio_info = AudioInfo(

            filename=str(path),

            sample_rate=sample_rate,

            channels=1,

            duration=len(waveform) / sample_rate,

            samples=len(waveform),

            format=info.format,

            subtype=info.subtype,

        )

        if waveform.size > 0:

            audio_info.peak = float(
                np.max(np.abs(waveform))
            )

            audio_info.rms = float(
                np.sqrt(
                    np.mean(
                        waveform ** 2
                    )
                )
            )

        return waveform, audio_info