from dataclasses import asdict

from backend.tts.voice.analyzer import VoiceAnalyzer
from backend.tts.voice.library import VoiceLibrary
from backend.tts.voice.preprocessor import VoicePreprocessor
from backend.tts.voice.profile import VoiceProfile
from backend.tts.voice.validator import VoiceValidator


class VoiceManager:

    def __init__(self):

        self.library = VoiceLibrary()

        self.preprocessor = VoicePreprocessor()

        self.analyzer = VoiceAnalyzer()

        self.validator = VoiceValidator()

    def register(
        self,
        profile: VoiceProfile,
    ):

        prepared = self.preprocessor.prepare(
            profile.reference_audio
        )

        profile.reference_audio = prepared

        metrics = self.analyzer.analyze(
            prepared
        )

        errors = self.validator.validate(
            metrics
        )

        if errors:

            raise ValueError(
                "\n".join(errors)
            )

        profile.duration = metrics.duration
        profile.sample_rate = metrics.sample_rate
        profile.channels = metrics.channels

        voices = self.library.load()

        voices.append(
            asdict(profile)
        )

        self.library.save(voices)

        return profile