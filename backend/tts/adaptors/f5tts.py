from __future__ import annotations

from pathlib import Path
from typing import List

import soundfile as sf

from f5_tts.api import F5TTS

from backend.tts.adapters.base import (
    BaseTTSAdapter,
    GenerationRequest,
    GenerationResult,
)


class F5TTSAdapter(BaseTTSAdapter):
    """
    Official F5-TTS adapter.

    Responsibilities
    ----------------
    • Model initialization
    • Speech generation
    • Speaker management
    • Statistics
    • Cleanup
    """

    def __init__(
        self,
        device: str = "auto",
    ):

        super().__init__(device=device)

        self.engine = None

        self.current_speaker = ""

        self.generated_count = 0

        self.last_duration = 0.0
    # --------------------------------------------------
    # Initialization
    # --------------------------------------------------

    def initialize(
        self,
    ) -> bool:

        if self.engine is not None:

            return True

        try:

            self.engine = F5TTS()

            self.initialized = True

            return True

        except Exception:

            self.engine = None

            self.initialized = False

            raise

    # --------------------------------------------------

    def shutdown(
        self,
    ):

        try:

            if hasattr(
                self.engine,
                "shutdown",
            ):

                self.engine.shutdown()

        except Exception:

            pass

        self.engine = None

        self.initialized = False

    # --------------------------------------------------
    # Speaker Management
    # --------------------------------------------------

    def available_speakers(
        self,
    ) -> List[str]:

        """
        F5-TTS currently performs zero-shot voice cloning.
        There are no built-in speaker profiles.

        This method exists for compatibility with the
        NarrationPanel voice selector.
        """

        return [
            "Reference Voice"
        ]

    # --------------------------------------------------

    def load_speaker(
        self,
        speaker_name: str,
    ):

        """
        Store selected speaker profile.

        Future versions may support multiple speakers.
        """

        self.current_speaker = speaker_name

        return True

    # --------------------------------------------------
    # Warmup
    # --------------------------------------------------

    def warmup(
        self,
    ):

        self.ensure_initialized()

        return True
    # --------------------------------------------------
    # Generation
    # --------------------------------------------------

    def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResult:

        self.ensure_initialized()

        self.validate_request(
            request
        )

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

        try:

            wav, sample_rate, _ = self.engine.infer(

                ref_file=request.reference_audio,

                ref_text=request.reference_text,

                gen_text=request.generation_text,

                file_wave=str(
                    output_audio
                ),

                file_spec=spec_file,

            )

        except Exception as exc:

            return GenerationResult(

                success=False,

                output_audio="",

                sample_rate=0,

                duration=0.0,

                metadata={

                    "engine": self.name(),

                    "version": self.version(),

                    "error": str(exc),

                },

            )

        duration = 0.0

        try:

            info = sf.info(
                output_audio
            )

            duration = (

                info.frames

                / info.samplerate

            )

        except Exception:

            try:

                if wav is not None:

                    duration = (

                        len(wav)

                        / sample_rate

                    )

            except Exception:

                duration = 0.0

        self.generated_count += 1

        self.last_duration = duration

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

                "speaker": self.current_speaker,

                "device": self.device,

                "generated_count": self.generated_count,

            },

        )
    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------

    def statistics(
        self,
    ):

        return {

            "initialized": self.initialized,

            "engine": self.name(),

            "version": self.version(),

            "device": self.device,

            "speaker": self.current_speaker,

            "generated_count": self.generated_count,

            "last_duration": self.last_duration,

            "loaded": self.is_loaded(),

        }

    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def cleanup(
        self,
    ):

        try:

            if hasattr(
                self.engine,
                "cleanup",
            ):

                self.engine.cleanup()

        except Exception:

            pass

    # --------------------------------------------------
    # Information
    # --------------------------------------------------

    def debug_info(
        self,
    ):

        return {

            "engine": self.name(),

            "version": self.version(),

            "device": self.device,

            "loaded": self.is_loaded(),

            "speaker": self.current_speaker,

            "generated": self.generated_count,

            "last_duration": self.last_duration,

        }

    # --------------------------------------------------
    # Reset Statistics
    # --------------------------------------------------

    def reset_statistics(
        self,
    ):

        self.generated_count = 0

        self.last_duration = 0.0

    # --------------------------------------------------
    # Status
    # --------------------------------------------------

    def ready(
        self,
    ):

        return self.initialized and self.engine is not None
    # --------------------------------------------------
    # Capabilities
    # --------------------------------------------------

    def supports_streaming(
        self,
    ) -> bool:

        return False

    def supports_voice_cloning(
        self,
    ) -> bool:

        return True

    def supports_multi_speaker(
        self,
    ) -> bool:

        return False

    def supports_reference_audio(
        self,
    ) -> bool:

        return True

    def supports_reference_text(
        self,
    ) -> bool:

        return True

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------

    def validate_engine(
        self,
    ):

        self.ensure_initialized()

        return self.engine is not None

    # --------------------------------------------------
    # Lifecycle
    # --------------------------------------------------

    def reset(
        self,
    ):

        self.cleanup()

        self.reset_statistics()

        self.current_speaker = ""

    # --------------------------------------------------
    # Destructor
    # --------------------------------------------------

    def __del__(
        self,
    ):

        try:

            self.shutdown()

        except Exception:

            pass