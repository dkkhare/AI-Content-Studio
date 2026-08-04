from pathlib import Path


class ModelManager:

    def __init__(self):

        self.model_dir = (
            Path.home()
            / ".ai_content_studio"
            / "models"
            / "f5tts"
        )

        self.model_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def exists(self):

        return any(self.model_dir.iterdir())

    def location(self):

        return self.model_dir