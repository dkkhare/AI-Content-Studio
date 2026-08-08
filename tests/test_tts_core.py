from __future__ import annotations

import tempfile
import unittest
import wave
from pathlib import Path

from backend.tts.adapters import F5TTSAdapter, GenerationRequest
from backend.tts.generator import TTSGenerator
from backend.tts.pipeline import TTSPipeline


def write_silent_wav(path: Path) -> None:
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(24000)
        output.writeframes(b"\\x00\\x00" * 240)


class TTSAdapterTests(unittest.TestCase):
    def test_lazy_adapter_uses_injected_runner(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            reference = root / "reference.wav"
            target = root / "nested" / "result.wav"
            write_silent_wav(reference)

            def runner(request):
                write_silent_wav(Path(request.output_audio))
                return request.output_audio

            adapter = F5TTSAdapter(runner=runner)
            self.assertFalse(adapter.statistics()["initialized"])
            result = adapter.generate(GenerationRequest(
                str(reference), "reference", "नमस्ते", str(target)
            ))
            self.assertEqual(Path(result.output_audio), target)
            self.assertTrue(target.is_file())
            self.assertEqual(adapter.statistics()["generated"], 1)

    def test_request_validation_rejects_missing_inputs(self):
        request = GenerationRequest("missing.wav", "", "", "out.wav")
        with self.assertRaises(FileNotFoundError):
            request.validate()


class TTSGeneratorTests(unittest.TestCase):
    def test_split_and_generate_are_deterministic(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            reference = root / "reference.wav"
            write_silent_wav(reference)

            def runner(request):
                write_silent_wav(Path(request.output_audio))
                return request.output_audio

            generator = TTSGenerator(F5TTSAdapter(runner), root / "output")
            generator.chunk_size = 8
            chunks = generator.split_text("first paragraph\nsecond paragraph")
            self.assertGreater(len(chunks), 1)
            outputs = generator.generate(chunks, str(reference), "reference")
            self.assertEqual(len(outputs), len(chunks))
            self.assertTrue(all(Path(path).is_file() for path in outputs))
            self.assertEqual(generator.progress_percent(), 100)


class TTSPipelineLifecycleTests(unittest.TestCase):
    def _session(self, pipeline, reference):
        return pipeline.create_session(
            reference_audio=reference,
            reference_text="reference",
            text="नमस्ते दुनिया",
        )

    def test_success_moves_session_to_history(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            reference = root / "reference.wav"
            write_silent_wav(reference)

            def runner(request):
                write_silent_wav(Path(request.output_audio))
                return request.output_audio

            pipeline = TTSPipeline(root / "output", adapter=F5TTSAdapter(runner))
            session = self._session(pipeline, reference)
            result = pipeline.run(session)
            self.assertEqual(result.status, "Completed")
            self.assertEqual(result.progress, 100)
            self.assertTrue(Path(result.output_file).is_file())
            self.assertIsNone(pipeline.queue.current())
            self.assertIn(session, pipeline.queue.history())

    def test_failure_marks_session_and_releases_queue(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            reference = root / "reference.wav"
            write_silent_wav(reference)

            def runner(request):
                raise RuntimeError("synthesis failed")

            pipeline = TTSPipeline(root / "output", adapter=F5TTSAdapter(runner))
            session = self._session(pipeline, reference)
            with self.assertRaisesRegex(RuntimeError, "synthesis failed"):
                pipeline.run(session)
            self.assertEqual(session.status, "Failed")
            self.assertEqual(session.error, "synthesis failed")
            self.assertIsNone(pipeline.queue.current())
            self.assertIn(session, pipeline.queue.history())

    def test_cancellation_is_not_reported_as_failure(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            reference = root / "reference.wav"
            write_silent_wav(reference)

            def runner(request):
                raise RuntimeError("Generation cancelled.")

            pipeline = TTSPipeline(root / "output", adapter=F5TTSAdapter(runner))
            session = self._session(pipeline, reference)
            with self.assertRaisesRegex(RuntimeError, "cancelled"):
                pipeline.run(session)
            self.assertEqual(session.status, "Cancelled")
            self.assertTrue(session.cancelled)
            self.assertEqual(session.error, "")
            self.assertIsNone(pipeline.queue.current())


if __name__ == "__main__":
    unittest.main()
