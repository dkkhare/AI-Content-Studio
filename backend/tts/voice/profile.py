from dataclasses import dataclass


@dataclass
class VoiceProfile:

    id: str

    name: str

    reference_audio: str

    language: str = "Unknown"

    duration: float = 0.0

    sample_rate: int = 0

    channels: int = 1

    quality_score: float = 0.0