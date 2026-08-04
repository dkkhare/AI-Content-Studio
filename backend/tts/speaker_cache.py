import json
from dataclasses import asdict
from pathlib import Path

from backend.tts.speaker_profile import SpeakerProfile


class SpeakerCache:
    """
    Manages cached speaker profiles.
    """

    def __init__(self, cache_directory="cache/speakers"):

        self.cache_directory = Path(cache_directory)

        self.cache_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def profile_directory(self, name):

        return self.cache_directory / name

    def save(self, profile: SpeakerProfile):

        directory = self.profile_directory(profile.name)

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        profile_file = directory / "speaker.json"

        with open(profile_file, "w", encoding="utf-8") as fp:

            json.dump(
                asdict(profile),
                fp,
                indent=4,
                ensure_ascii=False,
            )

    def load(self, name):

        profile_file = (
            self.profile_directory(name)
            / "speaker.json"
        )

        if not profile_file.exists():

            return None

        with open(profile_file, encoding="utf-8") as fp:

            data = json.load(fp)

        return SpeakerProfile(**data)

    def exists(self, name):

        return (
            self.profile_directory(name)
            / "speaker.json"
        ).exists()

    def delete(self, name):

        directory = self.profile_directory(name)

        if not directory.exists():

            return

        for file in directory.iterdir():

            file.unlink()

        directory.rmdir()

    def list_profiles(self):

        profiles = []

        for folder in self.cache_directory.iterdir():

            if folder.is_dir():

                profiles.append(folder.name)

        return sorted(profiles)