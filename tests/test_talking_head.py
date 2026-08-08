from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from backend.talking_head import (
    LongFormTalkingHeadPipeline,
    PodcastRequest,
    SadTalkerAdapter,
    SadTalkerConfig,
    split_script,
)


class TalkingHeadTests(unittest.TestCase):
    def test_split_script_preserves_text_and_bounds_chunks(self):
        source = "पहला वाक्य। दूसरा वाक्य थोड़ा लंबा है। Third sentence."
        chunks = split_script(source, segment_seconds=15, characters_per_second=4)
        self.assertGreaterEqual(len(chunks), 2)
        self.assertEqual(" ".join(chunks), source)

    def test_sadtalker_uses_argument_list_and_atomically_copies_result(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            repository = root / "SadTalker"
            repository.mkdir()
            (repository / "inference.py").write_text("# test", encoding="utf-8")
            portrait = root / "portrait.png"
            audio = root / "audio.wav"
            output = root / "segment.mp4"
            portrait.write_bytes(b"image")
            audio.write_bytes(b"audio")
            calls = []

            def runner(command, **kwargs):
                calls.append((command, kwargs))
                result_dir = Path(command[command.index("--result_dir") + 1])
                (result_dir / "generated.mp4").write_bytes(b"video")
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            result = SadTalkerAdapter(
                SadTalkerConfig(repository), runner=runner
            ).generate(portrait, audio, output)
            self.assertEqual(result, output.resolve())
            self.assertEqual(output.read_bytes(), b"video")
            self.assertIsInstance(calls[0][0], list)
            self.assertNotIn("shell", calls[0][1])
            self.assertFalse(output.with_suffix(".partial.mp4").exists())

    def test_pipeline_resumes_completed_segments(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            portrait = root / "portrait.png"
            reference = root / "voice.wav"
            portrait.write_bytes(b"image")
            reference.write_bytes(b"voice")
            tts_calls = []

            class TTS:
                def generate(self, request):
                    tts_calls.append(request.generation_text)
                    Path(request.output_audio).write_bytes(b"audio")
                    return SimpleNamespace(output_audio=request.output_audio)

            class TalkingHead:
                def generate(self, portrait, audio, output, **kwargs):
                    output.write_bytes(b"video")
                    return output

            def ffmpeg(command, **kwargs):
                Path(command[-1]).write_bytes(b"joined")
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            request = PodcastRequest(
                script="One sentence. Two sentence. Three sentence.",
                portrait=portrait,
                reference_audio=reference,
                reference_text="Voice transcript.",
                output=root / "output" / "podcast.mp4",
                work_directory=root / "work",
                segment_seconds=15,
            )
            pipeline = LongFormTalkingHeadPipeline(
                tts=TTS(), sadtalker=TalkingHead(), runner=ffmpeg
            )
            first = pipeline.run(request)
            second = pipeline.run(request)
            self.assertTrue(Path(first.output).is_file())
            self.assertEqual(second.resumed_segments, len(second.segments))
            self.assertEqual(len(tts_calls), len(first.segments))

    def test_request_rejects_missing_consent_inputs_and_bad_duration(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            portrait = root / "portrait.png"
            voice = root / "voice.wav"
            portrait.write_bytes(b"image")
            voice.write_bytes(b"voice")
            with self.assertRaisesRegex(ValueError, "transcript"):
                PodcastRequest(
                    "script", portrait, voice, "", root / "out.mp4", root / "work"
                ).validate()
            with self.assertRaisesRegex(ValueError, "between 1 and 180"):
                PodcastRequest(
                    "script", portrait, voice, "words", root / "out.mp4",
                    root / "work", target_minutes=0
                ).validate()


if __name__ == "__main__":
    unittest.main()
