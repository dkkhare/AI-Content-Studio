from backend.tts.inference.model_manager import ModelManager
from backend.tts.inference.voice_encoder import VoiceEncoder
from backend.tts.inference.text_processor import TextProcessor
from backend.tts.inference.validator import RuntimeValidator


class TTSRuntime:

    def __init__(self):

        self.models = ModelManager()

        self.encoder = VoiceEncoder()

        self.text = TextProcessor()

    def prepare(
        self,
        reference_audio,
        input_text,
    ):

        RuntimeValidator.validate_reference(
            reference_audio
        )

        embedding = self.encoder.encode(
            reference_audio
        )

        cleaned = self.text.normalize(
            input_text
        )

        return embedding, cleaned