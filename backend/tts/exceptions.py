"""
Exceptions for the Text-to-Speech subsystem.
"""


class TTSError(Exception):
    """
    Base exception for all TTS-related errors.
    """

    pass


class ModelNotInstalledError(TTSError):
    """
    Raised when the required TTS model is not installed.
    """

    pass


class ModelDownloadError(TTSError):
    """
    Raised when downloading a model fails.
    """

    pass


class ModelVerificationError(TTSError):
    """
    Raised when a downloaded model fails checksum verification.
    """

    pass


class InvalidReferenceAudioError(TTSError):
    """
    Raised when the reference voice sample is invalid.
    """

    pass


class UnsupportedAudioFormatError(TTSError):
    """
    Raised when the audio format is not supported.
    """

    pass


class AudioProcessingError(TTSError):
    """
    Raised when preprocessing or postprocessing audio fails.
    """

    pass


class DeviceNotSupportedError(TTSError):
    """
    Raised when the selected execution device is unavailable.
    """

    pass


class CUDAOutOfMemoryError(TTSError):
    """
    Raised when CUDA runs out of GPU memory.
    """

    pass


class SpeechGenerationError(TTSError):
    """
    Raised when speech synthesis fails.
    """

    pass


class ChunkGenerationError(TTSError):
    """
    Raised when generation of an individual text chunk fails.
    """

    pass


class ConfigurationError(TTSError):
    """
    Raised when the TTS configuration is invalid.
    """

    pass


class EnvironmentError(TTSError):
    """
    Raised when required dependencies are missing.
    """

    pass