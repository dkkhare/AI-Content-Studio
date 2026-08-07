from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.tts.providers.f5tts_runtime import F5TTSRuntime


class FakeF5Model:
    def __init__(self):
        self.calls = []

    def infer(self, **kwargs):
        self.calls.append(kwargs)
        Path(kwargs["file_wave"]).write_bytes(b"RIFFfake")
        return None


class FakeLoader:
    def __init__(self):
        self.model = FakeF5Model()

    def load(self):
        return self.model


class F5TTSRuntimeTests(unittest.TestCase):
    def test_generates_local_wave_using_reference_voice(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            voice = root / "hindi_voice.wav"
            voice.write_bytes(b"voice")
            voice.with_suffix(".txt").write_text("यह संदर्भ वाक्य है।", encoding="utf-8")
            output = root / "generated.wav"

            loader = FakeLoader()
            runtime = F5TTSRuntime(loader=loader)
            result = runtime.synthesize("नमस्ते दुनिया।", voice, output)

            self.assertEqual(Path(result), output.resolve())
            self.assertTrue(output.exists())
            call = loader.model.calls[0]
            self.assertEqual(call["ref_file"], str(voice.resolve()))
            self.assertEqual(call["ref_text"], "यह संदर्भ वाक्य है।")
            self.assertEqual(call["gen_text"], "नमस्ते दुनिया।")

    def test_missing_reference_voice_fails_clearly(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = F5TTSRuntime(loader=FakeLoader())
            with self.assertRaises(FileNotFoundError):
                runtime.synthesize("नमस्ते", Path(temp) / "missing.wav", Path(temp) / "out.wav")


if __name__ == "__main__":
    unittest.main()
