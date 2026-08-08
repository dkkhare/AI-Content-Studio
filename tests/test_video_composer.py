from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from backend.project.project import Project
from backend.video import ProjectVideoService, VideoComposer, VideoSpec


class VideoComposerTests(unittest.TestCase):
    def _assets(self, root):
        root = Path(root)
        image = root / "cover.png"
        audio = root / "narration.wav"
        subtitles = root / "captions.srt"
        image.write_bytes(b"image")
        audio.write_bytes(b"audio")
        subtitles.write_text("1\n00:00:00,000 --> 00:00:01,000\nनमस्ते\n", encoding="utf-8")
        return image, audio, subtitles

    def test_spec_validates_codec_safe_dimensions_and_duration(self):
        spec = VideoSpec(1280, 720, 25, 2501)
        self.assertEqual(spec.frame_count, 63)
        for values in ((1279, 720, 25, 1000), (1280, 719, 25, 1000), (1280, 720, 0, 1000), (1280, 720, 25, 0)):
            with self.assertRaises(ValueError):
                VideoSpec(*values)

    def test_plan_preserves_unicode_subtitles_and_exact_timeline(self):
        with tempfile.TemporaryDirectory() as root:
            image, audio, subtitles = self._assets(root)
            manifest = VideoComposer().plan(
                visual=image,
                audio=audio,
                subtitles=subtitles,
                duration_seconds=2.501,
                width=1280,
                height=720,
                fps=25,
            )
            self.assertEqual(manifest.spec.duration_ms, 2501)
            self.assertEqual(manifest.spec.frame_count, 63)
            self.assertEqual(manifest.visual.kind, "image")
            self.assertEqual(manifest.subtitles.kind, "subtitles")

    def test_missing_and_unsupported_assets_are_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            image, audio, _ = self._assets(root)
            with self.assertRaises(FileNotFoundError):
                VideoComposer().plan(visual=image, audio=Path(root) / "missing.wav", duration_seconds=1)
            bad = Path(root) / "cover.exe"
            bad.write_bytes(b"bad")
            with self.assertRaises(ValueError):
                VideoComposer().plan(visual=bad, audio=audio, duration_seconds=1)

    def test_manifest_write_is_atomic_json(self):
        with tempfile.TemporaryDirectory() as root:
            image, audio, subtitles = self._assets(root)
            manifest = VideoComposer().plan(
                visual=image, audio=audio, subtitles=subtitles, duration_seconds=1
            )
            output = manifest.write(Path(root) / "output" / "manifest.json")
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(data["spec"]["duration_ms"], 1000)
            self.assertFalse(output.with_suffix(".json.tmp").exists())


class ProjectVideoServiceTests(unittest.TestCase):
    def test_project_manifest_is_written_inside_project(self):
        with tempfile.TemporaryDirectory() as root:
            project = Project("Video", Path(root)).initialize()
            image = Path(root) / "cover.png"
            audio = Path(root) / "output" / "narration.wav"
            subtitles = Path(root) / "output" / "captions.srt"
            image.write_bytes(b"image")
            audio.write_bytes(b"audio")
            subtitles.write_text("captions", encoding="utf-8")
            manifest, output = ProjectVideoService().create_manifest(
                project,
                visual=image,
                audio=audio,
                subtitles=subtitles,
                duration_seconds=4,
            )
            self.assertTrue(output.is_file())
            self.assertEqual(manifest.spec.duration_ms, 4000)

    def test_project_path_escape_and_wrong_output_type_are_rejected(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as outside:
            project = Project("Video", Path(root)).initialize()
            external = Path(outside) / "cover.png"
            external.write_bytes(b"image")
            audio = Path(root) / "output" / "narration.wav"
            audio.write_bytes(b"audio")
            service = ProjectVideoService()
            with self.assertRaises(ValueError):
                service.create_manifest(project, visual=external, audio=audio, duration_seconds=1)
            inside = Path(root) / "cover.png"
            inside.write_bytes(b"image")
            with self.assertRaises(ValueError):
                service.create_manifest(
                    project, visual=inside, audio=audio, duration_seconds=1, output="output/video.txt"
                )


if __name__ == "__main__":
    unittest.main()
