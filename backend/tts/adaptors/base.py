from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any


@dataclass
class GenerationRequest:
    """
    Request passed to a TTS adapter.
    """

    reference_audio: str

    reference_text: str

    generation_text: str

    output_audio: str

    output_spectrogram: Optional[str] = None

    speed: float = 1.0

    temperature: float = 0.8

    seed: Optional[int] = None


@dataclass
class GenerationResult:
    """
    Result returned by a TTS adapter.
    """

    success: bool

    output_audio: str

    sample_rate: int

    duration: float

    message: str = ""

    metadata: Optional[dict] = None


class BaseTTSAdapter(ABC):
    """
    Base class for all TTS adapters.
    """

    def __init__(
        self,
        device: str = "auto",
    ):

        self.device = device

        self.initialized = False

    # --------------------------------------------------
    # Initialization
    # --------------------------------------------------

    @abstractmethod
    def initialize(self) -> bool:
        """
        Load the TTS model.
        """
        pass

    @abstractmethod
    def shutdown(self):
        """
        Release model resources.
        """
        pass

    # --------------------------------------------------
    # Information
    # --------------------------------------------------

    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def version(self) -> str:
        pass

    @abstractmethod
    def is_loaded(self) -> bool:
        pass

    # --------------------------------------------------
    # Generation
    # --------------------------------------------------

    @abstractmethod
    def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResult:
        """
        Generate speech.
        """
        pass

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------

    def validate_request(
        self,
        request: GenerationRequest,
    ):

        if not Path(request.reference_audio).exists():

            raise FileNotFoundError(
                request.reference_audio
            )

        if not request.reference_text.strip():

            raise ValueError(
                "Reference text cannot be empty."
            )

        if not request.generation_text.strip():

            raise ValueError(
                "Generation text cannot be empty."
            )

    # --------------------------------------------------
    # Optional Hooks
    # --------------------------------------------------

    def warmup(self):
        """
        Optional warm-up before first inference.
        """

        return True

    def unload(self):
        """
        Optional alias for shutdown().
        """

        self.shutdown()

    def supports_streaming(self) -> bool:

        return False

    def supports_voice_cloning(self) -> bool:

        return True

    def supports_multi_speaker(self) -> bool:

        return False

    # --------------------------------------------------
    # Utility
    # --------------------------------------------------

    def ensure_initialized(self):

        if not self.initialized:

            self.initialize()

    def __enter__(self):

        self.ensure_initialized()

        return self

    def __exit__(
        self,
        exc_type,
        exc_val,
        exc_tb,
    ):

        self.shutdown()