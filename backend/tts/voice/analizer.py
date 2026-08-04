import soundfile as sf

from backend.tts.voice.metrics import VoiceMetrics


class VoiceAnalyzer:

    def analyze(self, filename):

        audio, sample_rate = sf.read(filename)

        duration = len(audio) / sample_rate

        channels = 1

        if len(audio.shape) > 1:
            channels = audio.shape[1]

        return VoiceMetrics(
            duration=duration,
            sample_rate=sample_rate,
            channels=channels,
            rms_level=0.0,
            silence_percent=0.0,
            clipping_percent=0.0,
        )