from __future__ import annotations

import os


class ModelLoader:
    """Lazy loader for the locally installed F5-TTS Python API."""

    def __init__(self):
        self.loaded = False
        self.model = None

    def load(self):
        if self.loaded and self.model is not None:
            return self.model

        try:
            from f5_tts.api import F5TTS
        except ImportError as exc:
            raise RuntimeError(
                "F5-TTS is not installed in the current Python environment. "
                "Install the local F5-TTS package before generating narration."
            ) from exc

        kwargs = {}
        model_name = os.getenv("AI_CONTENT_STUDIO_F5TTS_MODEL", "").strip()
        checkpoint = os.getenv("AI_CONTENT_STUDIO_F5TTS_CHECKPOINT", "").strip()
        vocab = os.getenv("AI_CONTENT_STUDIO_F5TTS_VOCAB", "").strip()
        device = os.getenv("AI_CONTENT_STUDIO_F5TTS_DEVICE", "").strip()

        if model_name:
            kwargs["model"] = model_name
        if checkpoint:
            kwargs["ckpt_file"] = checkpoint
        if vocab:
            kwargs["vocab_file"] = vocab
        if device:
            kwargs["device"] = device

        self.model = F5TTS(**kwargs)
        self.loaded = True
        return self.model
