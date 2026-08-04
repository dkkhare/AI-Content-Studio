from dataclasses import dataclass


@dataclass
class TTSConfig:
    """
    Global TTS configuration.
    """

    provider: str = "F5-TTS"

    device: str = "cuda"

    model_directory: str = "models/f5tts"

    checkpoint_file: str = "model.safetensors"

    output_directory: str = "output/tts"

    sample_rate: int = 24000

    speed: float = 1.0

    temperature: float = 0.8

    chunk_length: int = 300

    silence_between_chunks_ms: int = 150

    normalize_audio: bool = True

    use_fp16: bool = True

    auto_download_model: bool = True

    keep_chunk_files: bool = False

    seed: int | None = None