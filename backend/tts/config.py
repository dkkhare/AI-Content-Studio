from dataclasses import dataclass
from pathlib import Path


@dataclass
class TTSConfig:
    """
    Configuration for the Text-to-Speech subsystem.
    """

    # --------------------------------------------------
    # Provider
    # --------------------------------------------------

    provider: str = "F5-TTS"

    # --------------------------------------------------
    # Device
    # --------------------------------------------------

    device: str = "auto"

    use_fp16: bool = True

    # --------------------------------------------------
    # Speech
    # --------------------------------------------------

    speed: float = 1.0

    temperature: float = 0.8

    max_sentence_length: int = 300

    sample_rate: int = 24000

    output_format: str = "wav"

    normalize_audio: bool = True

    remove_silence: bool = False

    # --------------------------------------------------
    # Chunking
    # --------------------------------------------------

    chunk_length: int = 180

    overlap_sentences: int = 1

    # --------------------------------------------------
    # Batch
    # --------------------------------------------------

    batch_size: int = 1

    # --------------------------------------------------
    # Model
    # --------------------------------------------------

    model_name: str = "F5-TTS"

    model_directory: str = str(
        Path("models") / "f5tts"
    )

    checkpoint_file: str = "model.safetensors"

    config_file: str = "config.json"

    # --------------------------------------------------
    # Voice
    # --------------------------------------------------

    reference_audio: str = ""

    speaker_cache: str = str(
        Path("cache") / "speakers"
    )

    # --------------------------------------------------
    # Output
    # --------------------------------------------------

    output_directory: str = str(
        Path("output") / "tts"
    )

    keep_chunks: bool = False

    # --------------------------------------------------
    # Runtime
    # --------------------------------------------------

    enable_progress: bool = True

    auto_download_model: bool = True

    verify_checksum: bool = True

    debug: bool = False