from pathlib import Path

from backend.tts.config import TTSConfig
from backend.tts.detector import DeviceDetector
from backend.tts.environment import TTSEnvironment
from backend.tts.validator import ReferenceAudioValidator
from backend.tts.downloader import ModelDownloader
from backend.tts.model_info import ModelInfo
from backend.tts.exceptions import (
    ModelNotInstalledError,
    InvalidReferenceAudioError,
)


class TTSManager:
    """
    Central manager for the TTS subsystem.

    Responsibilities
    ----------------
    - Load configuration
    - Detect CPU/GPU
    - Validate Python environment
    - Manage model files
    - Validate reference audio
    - Provide information to the UI

    NOTE:
    Actual speech generation is implemented in later milestones.
    """

    def __init__(
        self,
        model_directory="models/f5tts",
    ):

        self.config = TTSConfig()

        self.detector = DeviceDetector()

        self.environment = TTSEnvironment()

        self.validator = ReferenceAudioValidator()

        self.downloader = ModelDownloader(
            model_directory
        )

        self.device = None

        self.model = ModelInfo(
            model_directory=model_directory
        )

        self.initialized = False

    # --------------------------------------------------
    # Initialize
    # --------------------------------------------------

    def initialize(self):

        missing = self.environment.check()

        if missing:

            raise RuntimeError(
                "Missing Python modules: "
                + ", ".join(missing)
            )

        self.device = self.detector.detect()

        self._scan_model()

        self.initialized = True

        return True

    # --------------------------------------------------
    # Model Scan
    # --------------------------------------------------

    def _scan_model(self):

        checkpoint = (
            Path(self.model.model_directory)
            / "model.safetensors"
        )

        if checkpoint.exists():

            self.model.installed = True

            self.model.checkpoint = str(
                checkpoint
            )

        else:

            self.model.installed = False

            self.model.checkpoint = ""

    # --------------------------------------------------
    # Device
    # --------------------------------------------------

    def device_info(self):

        if self.device is None:

            self.device = self.detector.detect()

        return self.device

    # --------------------------------------------------
    # Model
    # --------------------------------------------------

    def model_info(self):

        self._scan_model()

        return self.model

    # --------------------------------------------------
    # Configuration
    # --------------------------------------------------

    def get_config(self):

        return self.config

    def update_config(self, **kwargs):

        for key, value in kwargs.items():

            if hasattr(self.config, key):

                setattr(
                    self.config,
                    key,
                    value,
                )

    # --------------------------------------------------
    # Reference Audio
    # --------------------------------------------------

    def validate_reference_audio(
        self,
        filename,
    ):

        if not self.validator.validate(
            filename
        ):

            raise InvalidReferenceAudioError(
                f"Invalid reference audio: {filename}"
            )

        return True

    # --------------------------------------------------
    # Model Installed
    # --------------------------------------------------

    def model_installed(self):

        self._scan_model()

        return self.model.installed

    # --------------------------------------------------
    # Checkpoint
    # --------------------------------------------------

    def checkpoint(self):

        self._scan_model()

        if not self.model.installed:

            raise ModelNotInstalledError(
                "F5-TTS model not installed."
            )

        return self.model.checkpoint

    # --------------------------------------------------
    # Download
    # --------------------------------------------------

    def download_model(
        self,
        url,
        filename,
        callback=None,
    ):

        path = self.downloader.download(
            url,
            filename,
            callback,
        )

        self._scan_model()

        return path

    # --------------------------------------------------
    # Status
    # --------------------------------------------------

    def status(self):

        return {

            "initialized": self.initialized,

            "device": self.device_info().device,

            "cuda": self.device_info().cuda_available,

            "gpu": self.device_info().gpu_name,

            "model_installed": self.model_installed(),

            "checkpoint": self.model.checkpoint,

        }

    # --------------------------------------------------
    # Reset
    # --------------------------------------------------

    def reset(self):

        self.initialized = False

        self.device = None

        self.model.installed = False

        self.model.checkpoint = ""