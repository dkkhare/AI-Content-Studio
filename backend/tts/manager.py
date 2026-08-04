from __future__ import annotations

from pathlib import Path
from typing import Optional


from backend.tts.config import TTSConfig

from backend.tts.adapters import (
    F5TTSAdapter,
)

from backend.tts.generator import (
    TTSGenerator,
)

from backend.tts.pipeline import (
    TTSPipeline,
)

from backend.tts.audio_merger import (
    AudioMerger,
)

from backend.tts.session import (
    TTSSession,
)

from backend.tts.exceptions import (
    ModelNotInstalledError,
    InvalidReferenceAudioError,
)


from backend.tts.detector import (
    DeviceDetector,
)

from backend.tts.environment import (
    TTSEnvironment,
)

from backend.tts.reference_manager import (
    ReferenceManager,
)

from backend.tts.validator import (
    ReferenceAudioValidator,
)

from backend.tts.text_cleaner import (
    TextCleaner,
)

from backend.tts.sentence_splitter import (
    SentenceSplitter,
)

from backend.tts.chunker import (
    TextChunker,
)



class TTSManager:
    """
    Central controller for AI Content Studio TTS system.

    Handles:

    - Configuration
    - Device detection
    - F5-TTS lifecycle
    - Reference voice
    - Text preparation
    - Pipeline access
    """


    def __init__(
        self,
        model_directory="models/f5tts",
        output_directory="output/tts",
    ):


        # -----------------------------------------
        # Configuration
        # -----------------------------------------

        self.config = TTSConfig()


        # -----------------------------------------
        # Environment
        # -----------------------------------------

        self.environment = TTSEnvironment()


        self.detector = DeviceDetector()


        self.device = None



        # -----------------------------------------
        # Validation
        # -----------------------------------------

        self.validator = (
            ReferenceAudioValidator()
        )


        # -----------------------------------------
        # Reference Voice
        # -----------------------------------------

        self.reference_manager = (
            ReferenceManager()
        )


        self.reference_audio_path = ""

        self.speaker = None



        # -----------------------------------------
        # Text Processing
        # -----------------------------------------

        self.cleaner = TextCleaner()


        self.splitter = SentenceSplitter()


        self.chunker = TextChunker(

            max_length=self.config.chunk_length

        )



        # -----------------------------------------
        # F5-TTS Adapter
        # -----------------------------------------

        self.adapter = F5TTSAdapter()



        # -----------------------------------------
        # Generation
        # -----------------------------------------

        self.generator = TTSGenerator(

            adapter=self.adapter,

            output_directory=output_directory,

        )


        self.merger = AudioMerger()



        # -----------------------------------------
        # Pipeline
        # -----------------------------------------

        self.pipeline = TTSPipeline(

            output_directory=output_directory

        )



        # -----------------------------------------
        # Model
        # -----------------------------------------

        self.model_directory = Path(
            model_directory
        )


        self.initialized = False


    # ==================================================
    # INITIALIZATION
    # ==================================================

    def initialize(self):


        missing = (
            self.environment.check()
        )


        if missing:

            raise RuntimeError(

                "Missing packages: "

                + ", ".join(missing)

            )


        self.device = (
            self.detector.detect()
        )


        self.adapter.initialize()


        self.initialized = True


        return True



    def shutdown(self):


        self.adapter.shutdown()


        self.initialized = False



    def is_initialized(self):

        return self.initialized



    # ==================================================
    # DEVICE
    # ==================================================

    def device_info(self):


        if self.device is None:

            self.device = (
                self.detector.detect()
            )


        return self.device