"""Provider contracts and optional F5-TTS adapter.

The desktop can import and configure narration without loading a heavyweight TTS
runtime. The F5 runtime is resolved only when generation is requested.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class GenerationRequest:
    reference_audio: str
    reference_text: str
    generation_text: str
    output_audio: str

    def validate(self) -> "GenerationRequest":
        if not Path(self.reference_audio).is_file():
            raise FileNotFoundError(f"Reference audio not found: {self.reference_audio}")
        if not self.reference_text.strip():
            raise ValueError("Reference transcript is required.")
        if not self.generation_text.strip():
            raise ValueError("Generation text is required.")
        if not self.output_audio.strip():
            raise ValueError("Output audio path is required.")
        return self


@dataclass(frozen=True, slots=True)
class GenerationResult:
    output_audio: str
    provider: str = "f5-tts"


@runtime_checkable
class BaseTTSAdapter(Protocol):
    def initialize(self) -> None: ...
    def generate(self, request: GenerationRequest) -> GenerationResult: ...
    def shutdown(self) -> None: ...


class F5TTSAdapter:
    """Lazy F5-TTS bridge with an injectable runner for tests and packaging."""

    def __init__(self, runner: Callable[[GenerationRequest], Any] | None = None):
        self._runner = runner
        self._runtime: Any = None
        self._initialized = False
        self._generated = 0

    def initialize(self) -> None:
        # Importing the desktop must not require the optional model runtime.
        self._initialized = True

    def _default_runner(self) -> Callable[[GenerationRequest], Any]:
        try:
            from f5_tts.api import F5TTS
        except ImportError as exc:
            raise RuntimeError(
                "F5-TTS runtime is not installed. Install the optional f5-tts "
                "dependency before generating narration."
            ) from exc

        if self._runtime is None:
            self._runtime = F5TTS()

        def run(request: GenerationRequest) -> str:
            self._runtime.infer(
                ref_file=request.reference_audio,
                ref_text=request.reference_text,
                gen_text=request.generation_text,
                file_wave=request.output_audio,
            )
            return request.output_audio

        return run

    def generate(self, request: GenerationRequest) -> GenerationResult:
        request.validate()
        if not self._initialized:
            self.initialize()

        output = Path(request.output_audio)
        output.parent.mkdir(parents=True, exist_ok=True)
        value = (self._runner or self._default_runner())(request)

        if isinstance(value, GenerationResult):
            result = value
        else:
            result = GenerationResult(str(value or output))

        if not Path(result.output_audio).is_file():
            raise RuntimeError("TTS runtime did not create the requested audio file.")

        self._generated += 1
        return result

    def available_speakers(self) -> list[str]:
        return []

    def load_speaker(self, speaker_name: str) -> None:
        if not isinstance(speaker_name, str):
            raise TypeError("Speaker name must be text.")

    def statistics(self) -> dict[str, Any]:
        return {
            "adapter": "f5-tts",
            "initialized": self._initialized,
            "generated": self._generated,
            "runtime_loaded": self._runtime is not None,
        }

    def cleanup(self) -> None:
        pass

    def shutdown(self) -> None:
        self._runtime = None
        self._initialized = False
