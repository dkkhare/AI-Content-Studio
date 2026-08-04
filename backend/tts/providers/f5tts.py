from backend.tts.base import TTSProvider
from backend.tts.result import TTSResult


class F5TTSProvider(TTSProvider):

    name = "F5-TTS"

    def load_model(self):
        """
        Load the F5-TTS model.
        """
        pass

    def clone_voice(self, voice_sample):

        self.voice = voice_sample

    def generate(
        self,
        text,
        output_file
    ):

        """
        Real implementation will call the
        F5-TTS inference pipeline.
        """

        return TTSResult(
            success=True,
            audio_file=output_file,
            duration=0,
            sample_rate=24000,
        )