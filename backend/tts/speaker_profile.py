from dataclasses import dataclass
from datetime import datetime


@dataclass
class SpeakerProfile:
    """
    Stores information about a processed speaker.
    """

    name: str = ""

    reference_audio: str = ""

    processed_audio: str = ""

    embedding_file: str = ""

    duration: float = 0.0

    sample_rate: int = 24000

    created: str = datetime.now().isoformat()

    model: str = "F5-TTS"

    language: str = "auto"

    notes: str = ""