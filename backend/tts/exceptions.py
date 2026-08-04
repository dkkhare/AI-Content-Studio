class TTSError(Exception):
    """Base TTS exception."""
    pass


class ModelNotInstalledError(TTSError):
    """Model checkpoint missing."""
    pass


class InvalidReferenceAudioError(TTSError):
    """Reference audio is invalid."""
    pass


class AudioGenerationError(TTSError):
    """Speech generation failed."""
    pass


class AudioMergeError(TTSError):
    """Audio merge failed."""
    pass


class PipelineError(TTSError):
    """Pipeline execution failed."""
    pass


class SessionCancelledError(TTSError):
    """Generation cancelled."""
    pass


class QueueEmptyError(TTSError):
    """Queue is empty."""
    pass