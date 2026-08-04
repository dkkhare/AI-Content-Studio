from dataclasses import dataclass


@dataclass
class AudioInfo:
    """
    Metadata describing an audio file.
    """

    filename: str = ""

    sample_rate: int = 0

    channels: int = 0

    duration: float = 0.0

    samples: int = 0

    format: str = ""

    subtype: str = ""

    bitrate: int = 0

    peak: float = 0.0

    rms: float = 0.0