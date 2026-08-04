from abc import ABC, abstractmethod

from backend.tts.result import TTSResult


class TTSProvider(ABC):

    name = "Unknown"

    @abstractmethod
    def load_model(self):
        pass

    @abstractmethod
    def clone_voice(self, voice_sample: str):
        pass

    @abstractmethod
    def generate(
        self,
        text: str,
        output_file: str
    ) -> TTSResult:
        pass