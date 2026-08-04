from backend.tts.audio import AudioProcessor


class VoicePreprocessor:

    def __init__(self):

        self.audio = AudioProcessor()

    def prepare(self, filename):

        filename = self.audio.normalize(filename)

        filename = self.audio.trim_silence(filename)

        return filename