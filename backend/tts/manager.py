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
    # ==================================================
    # MODEL MANAGEMENT
    # ==================================================

    def scan_model(self):

        checkpoint = (
            self.model_directory
            / self.config.checkpoint_file
        )

        return checkpoint.exists()


    def model_installed(self):

        return self.scan_model()


    def checkpoint(self):

        checkpoint = (

            self.model_directory

            / self.config.checkpoint_file

        )


        if not checkpoint.exists():

            raise ModelNotInstalledError(

                "F5-TTS model checkpoint not found."

            )


        return str(checkpoint)



    def model_info(self):

        return {

            "directory":
                str(self.model_directory),

            "installed":
                self.model_installed(),

            "checkpoint":

                str(self.checkpoint())

                if self.model_installed()

                else "",

        }


    # ==================================================
    # CONFIGURATION
    # ==================================================

    def get_config(self):

        return self.config



    def update_config(
        self,
        **kwargs
    ):


        for key, value in kwargs.items():

            if hasattr(
                self.config,
                key
            ):

                setattr(
                    self.config,
                    key,
                    value
                )


        self.chunker.max_length = (
            self.config.chunk_length
        )


        return self.config



    # ==================================================
    # REFERENCE AUDIO
    # ==================================================

    def set_reference_audio(
        self,
        filename,
    ):


        if not self.validator.validate(
            filename
        ):

            raise InvalidReferenceAudioError(

                filename

            )


        self.reference_audio_path = filename


        return True



    def reference_audio(self):

        return self.reference_audio_path



    # ==================================================
    # SPEAKER MANAGEMENT
    # ==================================================

    def prepare_reference(
        self,
        speaker_name="default",
    ):


        if not self.reference_audio_path:


            raise InvalidReferenceAudioError(

                "Reference audio not selected"

            )


        profile = (
            self.reference_manager.prepare(

                speaker_name,

                self.reference_audio_path,

            )
        )


        self.speaker = profile


        return profile



    def speaker_profile(self):

        return self.speaker



    def load_speaker(
        self,
        speaker_name,
    ):


        profile = (
            self.reference_manager.load_profile(
                speaker_name
            )
        )


        self.speaker = profile


        return profile



    def available_speakers(self):

        return (
            self.reference_manager.available_speakers()
        )



    def delete_speaker(
        self,
        speaker_name,
    ):


        self.reference_manager.delete_speaker(
            speaker_name
        )


        if (

            self.speaker

            and

            self.speaker.name == speaker_name

        ):

            self.speaker = None



    # ==================================================
    # TEXT PROCESSING
    # ==================================================

    def clean_text(
        self,
        text,
    ):


        text = (
            self.cleaner.clean(text)
        )


        return text



    def split_sentences(
        self,
        text,
    ):


        cleaned = (
            self.clean_text(text)
        )


        return (
            self.splitter.split(
                cleaned
            )
        )



    def create_chunks(
        self,
        text,
    ):


        sentences = (
            self.split_sentences(text)
        )


        return (
            self.chunker.chunk(
                sentences
            )
        )
    # ==================================================
    # STATUS
    # ==================================================

    def ready(self):

        return (

            self.initialized

            and

            self.speaker is not None

        )



    def status(self):

        return {

            "initialized":
                self.initialized,

            "provider":
                self.config.provider,

            "device":

                self.device.device

                if self.device

                else "unknown",


            "model_installed":
                self.model_installed(),


            "reference_audio":
                self.reference_audio_path,


            "speaker_loaded":

                self.speaker is not None,


            "ready":
                self.ready(),

        }



    def reset_runtime(self):


        self.reference_audio_path = ""

        self.speaker = None

        self.initialized = False

        self.device = None