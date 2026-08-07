from __future__ import annotations

from importlib import import_module


_EXPORTS = {
    "TTSConfig": ("backend.tts.config", "TTSConfig"),
    "TTSManager": ("backend.tts.manager", "TTSManager"),
    "TTSGenerator": ("backend.tts.generator", "TTSGenerator"),
    "TTSPipeline": ("backend.tts.pipeline", "TTSPipeline"),
    "TTSQueue": ("backend.tts.queue", "TTSQueue"),
    "TTSSession": ("backend.tts.session", "TTSSession"),
    "AudioMerger": ("backend.tts.audio_merger", "AudioMerger"),
}

__all__ = list(_EXPORTS)


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attribute = target
    module = import_module(module_name)
    value = getattr(module, attribute)
    globals()[name] = value
    return value
