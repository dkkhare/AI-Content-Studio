from dataclasses import dataclass


@dataclass
class ModelInfo:

    name: str = "F5-TTS"

    version: str = ""

    installed: bool = False

    model_directory: str = ""

    checkpoint: str = ""