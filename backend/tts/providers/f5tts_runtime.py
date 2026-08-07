from __future__ import annotations

from pathlib import Path

from backend.tts.model_loader import ModelLoader


class F5TTSRuntime:
    """Local F5-TTS runtime used for Hindi narration and podcast audio."""

    def __init__(self, loader: ModelLoader | None = None):
        self.loader = loader or ModelLoader()

    def initialize(self):
        return self.loader.load()

    @staticmethod
    def _reference_text(reference_audio: Path) -> str:
        sidecar = reference_audio.with_suffix(".txt")
        if sidecar.exists() and sidecar.is_file():
            return sidecar.read_text(encoding="utf-8").strip()
        return ""

    def synthesize(self, text, voice, output_file):
        text = str(text or "").strip()
        if not text:
            raise ValueError("F5-TTS cannot synthesize empty text.")

        reference_audio = Path(str(voice or "")).expanduser().resolve()
        if not reference_audio.exists() or not reference_audio.is_file():
            raise FileNotFoundError(
                "F5-TTS requires a local reference voice audio file. "
                f"Not found: {reference_audio}"
            )

        output = Path(output_file).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)

        model = self.initialize()
        ref_text = self._reference_text(reference_audio)

        try:
            model.infer(
                ref_file=str(reference_audio),
                ref_text=ref_text,
                gen_text=text,
                file_wave=str(output),
            )
        except Exception as exc:
            raise RuntimeError(f"F5-TTS synthesis failed: {exc}") from exc

        if not output.exists() or not output.is_file():
            raise RuntimeError(
                "F5-TTS inference returned without creating the expected WAV file: "
                f"{output}"
            )

        return str(output)
