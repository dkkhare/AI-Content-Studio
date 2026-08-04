from backend.tts.model_loader import ModelLoader


class F5TTSRuntime:

    def __init__(self):

        self.loader = ModelLoader()

    def initialize(self):

        if not self.loader.loaded:

            self.loader.load()

    def synthesize(
        self,
        text,
        voice,
        output_file,
    ):

        """
        Real implementation will call
        the F5-TTS inference API.

        Returns generated WAV.
        """

        return output_file