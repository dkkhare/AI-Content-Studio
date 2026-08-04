from pathlib import Path


class ReferenceAudioValidator:

    SUPPORTED = {
        ".wav",
        ".mp3",
        ".flac",
    }

    def validate(self, filename):

        path = Path(filename)

        if not path.exists():

            return False

        return path.suffix.lower() in self.SUPPORTED