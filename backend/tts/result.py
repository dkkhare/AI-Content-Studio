from dataclasses import dataclass


@dataclass
class TTSResult:
    success: bool
    audio_file: str
    duration: float
    sample_rate: int