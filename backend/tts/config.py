from dataclasses import dataclass


@dataclass
class TTSConfig:

    provider: str = "F5-TTS"

    device: str = "cuda"

    speed: float = 1.0

    temperature: float = 0.8

    max_sentence_length: int = 300