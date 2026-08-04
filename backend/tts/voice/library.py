import json
from pathlib import Path


class VoiceLibrary:

    def __init__(self):

        self.file = (
            Path.home()
            / ".ai_content_studio"
            / "voices.json"
        )

        self.file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def load(self):

        if not self.file.exists():

            return []

        return json.loads(
            self.file.read_text(
                encoding="utf-8"
            )
        )

    def save(self, voices):

        self.file.write_text(
            json.dumps(
                voices,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )