from dataclasses import dataclass


@dataclass
class VoiceMetrics:

    duration: float

    sample_rate: int

    channels: int

    rms_level: float

    silence_percent: float

    clipping_percent: float