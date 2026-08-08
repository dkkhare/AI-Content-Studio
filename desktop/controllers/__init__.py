from __future__ import annotations

__all__ = ["AIDesktopController", "TTSController"]


def __getattr__(name):
    if name == "AIDesktopController":
        from .ai_controller import AIDesktopController
        return AIDesktopController
    if name == "TTSController":
        from .tts_controller import TTSController
        return TTSController
    raise AttributeError(name)
