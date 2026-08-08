from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.project.project import Project
from backend.subtitles import (
    SubtitleCue,
    SubtitleDocument,
    ProjectSubtitleService,
    SubtitleGenerator,
    parse_srt,
    parse_timestamp,
    parse_vtt,
    read_subtitles,
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


class SubtitleParsingTests(unittest.TestCase):
    def test_srt_and_vtt_round_trip_multiline_unicode(self):
        original = SubtitleDocument([
            SubtitleCue(1, 0, 1250, "पहली पंक्ति\nदूसरी पंक्ति"),
            SubtitleCue(2, 1500, 3000, "समाप्त"),
        ])
        srt = parse_srt(original.to_srt())
        vtt = parse_vtt(original.to_vtt())
        self.assertEqual(srt.cues, original.cues)
        self.assertEqual(vtt.cues, original.cues)

    def test_vtt_identifier_settings_notes_and_bom(self):
        value = (
            "\ufeffWEBVTT\n\nNOTE generated\nignore this\n\n"
            "cue-one\n00:00:00.000 --> 00:00:01.000 align:start\nनमस्ते\n"
        )
        document = parse_vtt(value)
        self.assertEqual(len(document.cues), 1)
        self.assertEqual(document.cues[0].text, "नमस्ते")

    def test_malformed_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            parse_timestamp("00:99:00,000")
        with self.assertRaises(ValueError):
            parse_srt("2\n00:00:00,000 --> 00:00:01,000\nbad index")
        with self.assertRaises(ValueError):
            parse_vtt("00:00:00.000 --> 00:00:01.000\nmissing header")


class ProjectSubtitleServiceTests(unittest.TestCase):
    def test_generate_registers_atomic_project_asset(self):
        with tempfile.TemporaryDirectory() as root:
            project = Project("Subtitle Test", Path(root)).initialize()
            before = project.modified
            service = ProjectSubtitleService(SubtitleGenerator(max_chars=18, gap_ms=50))
            document = service.generate(
                project,
                "यह पहला वाक्य है। यह दूसरा वाक्य है।",
                audio_duration_seconds=6,
            )
            target = Path(project.subtitle_file)
            self.assertTrue(target.is_file())
            self.assertEqual(target.parent, project.output_path().resolve())
            self.assertEqual(read_subtitles(target).cues, document.cues)
            self.assertNotEqual(project.modified, before)
            self.assertFalse(target.with_suffix(".srt.tmp").exists())

    def test_import_normalizes_and_registers_subtitles(self):
        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)
            source = root_path / "incoming.vtt"
            source.write_text(
                "WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nHello\n",
                encoding="utf-8",
            )
            project = Project("Import Test", root_path / "project").initialize()
            document = ProjectSubtitleService().import_file(project, source)
            target = Path(project.subtitle_file)
            self.assertEqual(target.name, "subtitles.vtt")
            self.assertEqual(document.cues[0].text, "Hello")
            self.assertTrue(target.is_file())

    def test_output_escape_and_empty_text_are_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            project = Project("Unsafe", Path(root)).initialize()
            project.output_directory = "../outside"
            with self.assertRaises(ValueError):
                ProjectSubtitleService().generate(
                    project, "text", audio_duration_seconds=2
                )

            project.output_directory = "output"
            with self.assertRaises(ValueError):
                ProjectSubtitleService().generate(
                    project, "", audio_duration_seconds=2
                )


if __name__ == "__main__":
    unittest.main()
