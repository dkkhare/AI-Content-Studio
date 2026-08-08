from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.subtitles import (
    SubtitleCue,
    SubtitleDocument,
    SubtitleGenerator,
    format_timestamp,
)


class SubtitleCoreTests(unittest.TestCase):
    def test_timestamp_formats_are_spec_compliant(self):
        self.assertEqual(format_timestamp(3_723_045), "01:02:03,045")
        self.assertEqual(format_timestamp(3_723_045, vtt=True), "01:02:03.045")

    def test_hindi_text_is_split_without_losing_words(self):
        text = "यह पहला वाक्य है। यह दूसरा वाक्य थोड़ा लंबा है और ठीक से विभाजित होना चाहिए।"
        generator = SubtitleGenerator(max_chars=32)
        chunks = generator.split_text(text)
        self.assertGreater(len(chunks), 1)
        self.assertEqual(" ".join(chunks).split(), text.split())
        self.assertTrue(all(chunk.strip() for chunk in chunks))

    def test_audio_duration_allocation_is_exact_and_non_overlapping(self):
        document = SubtitleGenerator(max_chars=20, gap_ms=100).generate(
            "one two three four five six seven eight nine ten",
            total_duration_seconds=8,
        )
        self.assertGreater(len(document.cues), 1)
        self.assertEqual(document.cues[-1].end_ms, 8000)
        for first, second in zip(document.cues, document.cues[1:]):
            self.assertLessEqual(first.end_ms, second.start_ms)

    def test_srt_vtt_and_atomic_write(self):
        document = SubtitleDocument([
            SubtitleCue(1, 0, 1250, "नमस्ते"),
            SubtitleCue(2, 1330, 2500, "दुनिया"),
        ])
        self.assertIn("00:00:00,000 --> 00:00:01,250", document.to_srt())
        self.assertTrue(document.to_vtt().startswith("WEBVTT\n"))
        with tempfile.TemporaryDirectory() as root:
            srt = document.write(Path(root) / "subtitles.srt")
            vtt = document.write(Path(root) / "subtitles.vtt")
            self.assertIn("नमस्ते", srt.read_text(encoding="utf-8"))
            self.assertIn("00:00:01.330", vtt.read_text(encoding="utf-8"))
            self.assertFalse((Path(root) / "subtitles.srt.tmp").exists())

    def test_invalid_cues_and_too_short_duration_are_rejected(self):
        with self.assertRaises(ValueError):
            SubtitleCue(1, 100, 100, "bad")
        with self.assertRaises(ValueError):
            SubtitleDocument([
                SubtitleCue(1, 0, 1000, "one"),
                SubtitleCue(2, 900, 1500, "overlap"),
            ])
        with self.assertRaises(ValueError):
            SubtitleGenerator(max_chars=10).generate(
                "one two three four five six", total_duration_seconds=0.1
            )


if __name__ == "__main__":
    unittest.main()
