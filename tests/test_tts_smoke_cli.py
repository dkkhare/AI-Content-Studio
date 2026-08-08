from __future__ import annotations

import argparse
import io
import json
import tempfile
import unittest
from pathlib import Path

from backend.tts.session import TTSSession
from scripts.tts_smoke import run


class FakePipeline:
    def __init__(self, fail=False):
        self.fail = fail
        self.cleaned = False
        self.stopped = False

    def create_session(self, **kwargs):
        return TTSSession(
            reference_audio=str(kwargs["reference_audio"]),
            reference_text=kwargs["reference_text"],
            input_text=kwargs["text"],
            output_directory=str(kwargs["output_directory"]),
            language=kwargs["language"],
        )

    def run(self, session):
        if self.fail:
            session.fail("runtime unavailable")
            raise RuntimeError("runtime unavailable")
        target = Path(session.output_directory) / "smoke.wav"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"RIFF")
        session.output_file = str(target)
        session.generated_chunks = [str(target.with_name("chunk.wav"))]
        session.duration = 1.25
        session.complete()
        return session

    def cleanup_chunks(self, session):
        self.cleaned = True

    def shutdown(self):
        self.stopped = True


def args(reference, **overrides):
    values = {
        "reference_audio": str(reference),
        "reference_text": "reference",
        "text": "नमस्ते",
        "output": str(Path(reference).parent / "output"),
        "language": "hi",
        "keep_chunks": False,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


class TTSSmokeCLITests(unittest.TestCase):
    def test_success_returns_json_and_cleans_chunks(self):
        with tempfile.TemporaryDirectory() as root:
            reference = Path(root) / "voice.wav"
            reference.write_bytes(b"RIFF")
            pipeline = FakePipeline()
            output = io.StringIO()
            code = run(args(reference), pipeline=pipeline, stdout=output)
            payload = json.loads(output.getvalue())
            self.assertEqual(code, 0)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["language"], "hi")
            self.assertTrue(pipeline.cleaned)
            self.assertTrue(pipeline.stopped)

    def test_runtime_failure_is_reported_without_traceback(self):
        with tempfile.TemporaryDirectory() as root:
            reference = Path(root) / "voice.wav"
            reference.write_bytes(b"RIFF")
            pipeline = FakePipeline(fail=True)
            output = io.StringIO()
            self.assertEqual(run(args(reference), pipeline=pipeline, stdout=output), 3)
            payload = json.loads(output.getvalue())
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["status"], "Failed")
            self.assertTrue(pipeline.stopped)

    def test_missing_reference_returns_two_before_pipeline(self):
        output = io.StringIO()
        self.assertEqual(run(args("missing.wav"), stdout=output), 2)
        self.assertEqual(json.loads(output.getvalue())["error"], "reference audio not found")


if __name__ == "__main__":
    unittest.main()
