from pathlib import Path
from typing import Optional

from backend.tts.config import TTSConfig
from backend.tts.detector import DeviceDetector
from backend.tts.environment import TTSEnvironment
from backend.tts.validator import ReferenceAudioValidator
from backend.tts.downloader import ModelDownloader
from backend.tts.model_info import ModelInfo
from backend.tts.reference_manager import ReferenceManager
from backend.tts.text_cleaner import TextCleaner
from backend.tts.sentence_splitter import SentenceSplitter
from backend.tts.chunker import TextChunker

from backend.tts.exceptions import (
    ModelNotInstalledError,
    InvalidReferenceAudioError,
)


class TTSManager:
    """
    Central Text-to-Speech manager.

    Responsibilities
    ----------------
    • Environment validation
    • GPU detection
    • Configuration management
    • Model management
    • Reference voice preparation
    • Text preprocessing
    • Speech generation (later milestones)
    """

    def __init__(
        self,
        model_directory="models/f5tts",
    ):

        # --------------------------------------------------
        # Configuration
        # --------------------------------------------------

        self.config = TTSConfig()

        # --------------------------------------------------
        # Hardware
        # --------------------------------------------------

        self.detector = DeviceDetector()

        self.environment = TTSEnvironment()

        # --------------------------------------------------
        # Validation
        # --------------------------------------------------

        self.validator = ReferenceAudioValidator()

        # --------------------------------------------------
        # Download Manager
        # --------------------------------------------------

        self.downloader = ModelDownloader(
            model_directory
        )

        # --------------------------------------------------
        # Reference Voice
        # --------------------------------------------------

        self.reference_manager = ReferenceManager()

        # --------------------------------------------------
        # Text Pipeline
        # --------------------------------------------------

        self.cleaner = TextCleaner()

        self.splitter = SentenceSplitter()

        self.chunker = TextChunker(
            max_length=self.config.chunk_length,
        )

        # --------------------------------------------------
        # Runtime
        # --------------------------------------------------

        self.device = None

        self.reference_audio_path = ""

        self.speaker = None

        self.initialized = False

        # --------------------------------------------------
        # Model Information
        # --------------------------------------------------

        self.model = ModelInfo(
            model_directory=model_directory,
        )

    # ======================================================
    # INITIALIZATION
    # ======================================================

    def initialize(self):

        """
        Initialize TTS subsystem.
        """

        missing = self.environment.check()

        if missing:

            raise RuntimeError(

                "Missing Python packages: "

                + ", ".join(missing)

            )

        self.device = self.detector.detect()

        self.scan_model()

        self.initialized = True

        return True

    # ======================================================
    # ENVIRONMENT
    # ======================================================

    def check_environment(self):

        """
        Returns list of missing packages.
        """

        return self.environment.check()

    # ======================================================
    # DEVICE
    # ======================================================

    def device_info(self):

        if self.device is None:

            self.device = self.detector.detect()

        return self.device

    # ======================================================
    # INITIALIZATION STATUS
    # ======================================================

    def is_initialized(self):

        return self.initialized
    # ======================================================
    # MODEL
    # ======================================================

    def scan_model(self):
        """
        Scan the configured model directory and update model
        information.
        """

        model_dir = Path(self.model.model_directory)

        if not model_dir.exists():

            self.model.installed = False

            self.model.checkpoint = ""

            return False

        checkpoint = (
            model_dir /
            self.config.checkpoint_file
        )

        if checkpoint.exists():

            self.model.installed = True

            self.model.checkpoint = str(
                checkpoint
            )

        else:

            self.model.installed = False

            self.model.checkpoint = ""

        return self.model.installed

    # ======================================================
    # MODEL INFORMATION
    # ======================================================

    def model_info(self):
        """
        Return current model information.
        """

        self.scan_model()

        return self.model

    # ======================================================
    # MODEL STATUS
    # ======================================================

    def model_installed(self):
        """
        Returns True if a valid model checkpoint exists.
        """

        return self.scan_model()

    # ======================================================
    # CHECKPOINT
    # ======================================================

    def checkpoint(self):
        """
        Returns checkpoint path.
        """

        if not self.scan_model():

            raise ModelNotInstalledError(
                "F5-TTS model is not installed."
            )

        return self.model.checkpoint

    # ======================================================
    # MODEL DIRECTORY
    # ======================================================

    def model_directory(self):
        """
        Returns model directory.
        """

        return Path(
            self.model.model_directory
        )

    # ======================================================
    # VERIFY MODEL
    # ======================================================

    def verify_model(self):
        """
        Verify that all required model files exist.
        """

        if not self.scan_model():

            return False

        checkpoint = Path(
            self.model.checkpoint
        )

        if not checkpoint.exists():

            return False

        return True
    # ======================================================
    # CONFIGURATION
    # ======================================================

    def get_config(self):
        """
        Returns the current TTS configuration.
        """

        return self.config

    def update_config(self, **kwargs):
        """
        Update configuration values.
        """

        for key, value in kwargs.items():

            if hasattr(self.config, key):

                setattr(
                    self.config,
                    key,
                    value,
                )

        # Update chunker if chunk length changes
        self.chunker.max_length = (
            self.config.chunk_length
        )

        return self.config

    # ======================================================
    # DOWNLOAD MODEL
    # ======================================================

    def download_model(
        self,
        url,
        filename,
        callback=None,
    ):
        """
        Download model files.
        """

        downloaded = self.downloader.download(
            url=url,
            filename=filename,
            callback=callback,
        )

        self.scan_model()

        return downloaded

    # ======================================================
    # DELETE MODEL
    # ======================================================

    def delete_model(self):
        """
        Remove all downloaded model files.
        """

        self.downloader.clear()

        self.model.installed = False

        self.model.checkpoint = ""

        return True

    # ======================================================
    # STATUS
    # ======================================================

    def status(self):
        """
        Return current TTS subsystem status.
        """

        device = self.device_info()

        self.scan_model()

        return {

            "initialized": self.initialized,

            "provider": self.config.provider,

            "device": device.device,

            "cuda_available": device.cuda_available,

            "gpu_name": device.gpu_name,

            "gpu_memory_gb": device.total_memory_gb,

            "fp16_supported": device.fp16_supported,

            "model_installed": self.model.installed,

            "checkpoint": self.model.checkpoint,

            "model_directory": self.model.model_directory,

            "reference_audio": self.reference_audio_path,

            "speaker_loaded": self.speaker is not None,

        }

    # ======================================================
    # RESET
    # ======================================================

    def reset_runtime(self):
        """
        Reset runtime state without deleting the model.
        """

        self.reference_audio_path = ""

        self.speaker = None

        self.initialized = False

        self.device = None

        return True
    # ======================================================
    # REFERENCE AUDIO
    # ======================================================

    def set_reference_audio(self, filename):
        """
        Set reference audio file.
        """

        self.validator.validate(filename)

        self.reference_audio_path = filename

        return True

    def reference_audio(self):
        """
        Return current reference audio path.
        """

        return self.reference_audio_path

    # ======================================================
    # SPEAKER PREPARATION
    # ======================================================

    def prepare_reference(
        self,
        speaker_name="default",
    ):
        """
        Prepare reference audio for voice cloning.
        """

        if not self.reference_audio_path:

            raise InvalidReferenceAudioError(
                "Reference audio not selected."
            )

        profile = self.reference_manager.prepare(
            speaker_name=speaker_name,
            reference_audio=self.reference_audio_path,
        )

        self.speaker = profile

        return profile

    # ======================================================
    # SPEAKER
    # ======================================================

    def speaker_profile(self):
        """
        Return loaded speaker profile.
        """

        return self.speaker

    def load_speaker(
        self,
        speaker_name,
    ):

        profile = self.reference_manager.load_profile(
            speaker_name
        )

        self.speaker = profile

        return profile

    def available_speakers(self):

        return self.reference_manager.available_speakers()

    def delete_speaker(
        self,
        speaker_name,
    ):

        if (
            self.speaker is not None
            and self.speaker.name == speaker_name
        ):

            self.speaker = None

        self.reference_manager.delete_speaker(
            speaker_name
        )

    def clear_speaker_cache(self):

        self.speaker = None

        self.reference_audio_path = ""

    # ======================================================
    # TEXT PREPARATION
    # ======================================================

    def clean_text(
        self,
        text,
    ):

        text = self.cleaner.remove_control_characters(
            text
        )

        text = self.cleaner.normalize_quotes(
            text
        )

        text = self.cleaner.clean(
            text,
            preserve_stanzas=True,
        )

        return text

    def split_sentences(
        self,
        text,
    ):

        text = self.clean_text(text)

        return self.splitter.split(text)

    def create_chunks(
        self,
        text,
    ):

        sentences = self.split_sentences(
            text
        )

        return self.chunker.chunk(
            sentences
        )

    # ======================================================
    # INFORMATION
    # ======================================================

    def ready(self):
        """
        Returns True when the manager is ready
        for speech generation.
        """

        return (
            self.initialized
            and self.model_installed()
            and self.speaker is not None
        )

    def summary(self):

        return {

            "initialized": self.initialized,

            "model_installed": self.model_installed(),

            "reference_audio": self.reference_audio_path,

            "speaker":

                None

                if self.speaker is None

                else self.speaker.name,

            "device":

                self.device.device

                if self.device

                else "unknown",

            "provider":

                self.config.provider,

        }