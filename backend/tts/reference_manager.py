from pathlib import Path
import shutil

from backend.tts.audio_loader import AudioLoader
from backend.tts.audio_processor import AudioProcessor
from backend.tts.speaker_cache import SpeakerCache
from backend.tts.speaker_profile import SpeakerProfile


class ReferenceManager:
    """
    Handles reference voice preparation.
    """

    def __init__(self):

        self.loader = AudioLoader()

        self.processor = AudioProcessor()

        self.cache = SpeakerCache()

    def prepare(
        self,
        speaker_name,
        reference_audio,
    ):

        waveform, info = self.loader.load(
            reference_audio
        )

        processed = self.processor.process(
            waveform,
            info.sample_rate,
        )

        speaker_dir = (
            self.cache.profile_directory(
                speaker_name
            )
        )

        speaker_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        processed_file = (
            speaker_dir
            / "processed.wav"
        )

        self.processor.save(
            processed,
            processed_file,
        )

        reference_copy = (
            speaker_dir
            / Path(reference_audio).name
        )

        if not reference_copy.exists():

            shutil.copy2(
                reference_audio,
                reference_copy,
            )

        profile = SpeakerProfile(

            name=speaker_name,

            reference_audio=str(
                reference_copy
            ),

            processed_audio=str(
                processed_file
            ),

            duration=info.duration,

            sample_rate=24000,

        )

        self.cache.save(profile)

        return profile

    def load_profile(
        self,
        speaker_name,
    ):

        return self.cache.load(
            speaker_name
        )

    def available_speakers(self):

        return self.cache.list_profiles()

    def delete_speaker(
        self,
        speaker_name,
    ):

        self.cache.delete(
            speaker_name
        )