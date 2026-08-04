import librosa
import numpy as np
import soundfile as sf


class AudioProcessor:
    """
    Audio preprocessing for F5-TTS.

    Features
    --------
    • Resample
    • Normalize
    • Trim silence
    • Peak limiting
    • Save processed audio
    """

    def resample(

        self,

        waveform,

        original_rate,

        target_rate=24000,

    ):

        if original_rate == target_rate:

            return waveform

        return librosa.resample(

            waveform,

            orig_sr=original_rate,

            target_sr=target_rate,

        )

    def normalize(

        self,

        waveform,

        target_peak=0.95,

    ):

        peak = np.max(

            np.abs(waveform)

        )

        if peak == 0:

            return waveform

        return waveform * (

            target_peak / peak

        )

    def trim_silence(

        self,

        waveform,

        top_db=30,

    ):

        trimmed, _ = librosa.effects.trim(

            waveform,

            top_db=top_db,

        )

        return trimmed

    def peak_limit(

        self,

        waveform,

        limit=0.98,

    ):

        waveform = np.clip(

            waveform,

            -limit,

            limit,

        )

        return waveform

    def process(

        self,

        waveform,

        sample_rate,

        target_rate=24000,

        normalize=True,

        trim=True,

    ):

        waveform = self.resample(

            waveform,

            sample_rate,

            target_rate,

        )

        if trim:

            waveform = self.trim_silence(

                waveform

            )

        if normalize:

            waveform = self.normalize(

                waveform

            )

        waveform = self.peak_limit(

            waveform

        )

        return waveform

    def save(

        self,

        waveform,

        filename,

        sample_rate=24000,

    ):

        sf.write(

            filename,

            waveform,

            sample_rate,

        )