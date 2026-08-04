from pathlib import Path


class TTSCache:

    def __init__(self):

        self.path = Path(".cache/tts")

        self.path.mkdir(
            parents=True,
            exist_ok=True,
        )

    def filename(self, key):

        return self.path / f"{key}.wav"