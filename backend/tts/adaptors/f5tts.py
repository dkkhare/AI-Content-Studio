from __future__ import annotations

from pathlib import Path
import soundfile as sf

from f5_tts.api import F5TTS

from backend.tts.adapters.base import (
    BaseTTSAdapter,
    GenerationRequest,
    GenerationResult,
)


class F5TTSAdapter(BaseTTSAdapter):
    """
    Adapter for the official F5-TTS API.
    """

    def __init__(
        self,
        device: str = "auto",
    ):

        super().__init__(device=device)

        self.engine = None

    # --------------------------------------------------
    # Information
    # --------------------------------------------------

    def name(self) -> str:

        return "F5-TTS"

    def version(self) -> str:

        try:

            import f5_tts

            return getattr(
                f5_tts,
                "__version__",
                "Unknown",
            )

        except Exception:

            return "Unknown"

    def is_loaded(self) -> bool:

        return self.engine is not None

    # --------------------------------------------------
    # Initialization
    # --------------------------------------------------

    def initialize(self) -> bool:

        if self.engine is not None:

            return True

        self.engine = F5TTS()

        self.initialized = True

        return True

    def shutdown(self):

        self.engine = None

        self.initialized = False

    # --------------------------------------------------
    # Generation
    # --------------------------------------------------

    def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResult:

        self.ensure_initialized()

        self.validate_request(request)

        output_audio = Path(
            request.output_audio
        )

        output_audio.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        spec_file = None

        if request.output_spectrogram:

            spec_file = (
                request.output_spectrogram
            )

        # ------------------------------------------
        # Official F5-TTS inference
        # ------------------------------------------

        wav, sample_rate, _ = self.engine.infer(

            ref_file=request.reference_audio,

            ref_text=request.reference_text,

            gen_text=request.generation_text,

            file_wave=str(output_audio),

            file_spec=spec_file,

        )

        duration = 0.0

        try:

            info = sf.info(output_audio)

            duration = info.frames / info.samplerate

        except Exception:

            if wav is not None:

                duration = (
                    len(wav)
                    / sample_rate
                )

        return GenerationResult(

            success=True,

            output_audio=str(
                output_audio
            ),

            sample_rate=sample_rate,

            duration=duration,

            metadata={

                "engine": self.name(),

                "version": self.version(),

            },

        )

    # --------------------------------------------------
    # Warm-up
    # --------------------------------------------------

    def warmup(self):

        self.ensure_initialized()

        return True

    # --------------------------------------------------
    # Capabilities
    # --------------------------------------------------

    def supports_streaming(self) -> bool:

        return False

    def supports_voice_cloning(self) -> bool:

        return True

    def supports_multi_speaker(self) -> bool:

        return False