from __future__ import annotations

__all__ = [
    "TTSConfig",
    "TTSManager",
    "TTSGenerator",
    "TTSPipeline",
    "TTSQueue",
    "TTSSession",
    "AudioMerger",
]

_EXPORTS = {
    "TTSConfig": (".config", "TTSConfig"),
    "TTSManager": (".manager", "TTSManager"),
    "TTSGenerator": (".generator", "TTSGenerator"),
    "TTSPipeline": (".pipeline", "TTSPipeline"),
    "TTSQueue": (".queue", "TTSQueue"),
    "TTSSession": (".session", "TTSSession"),
    "AudioMerger": (".audio_merger", "AudioMerger"),
}


def __getattr__(name):
    try:
        module_name, attribute = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(name) from exc
    from importlib import import_module
    return getattr(import_module(module_name, __name__), attribute)
