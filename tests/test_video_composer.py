from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from threading import Event

from backend.project.project import Project
from backend.video import (
    FFmpegCommandBuilder,
    FFmpegRenderer,
    FFmpegRenderError,
    ProjectVideoService,
    RenderCancelled,
    VideoComposer,
    VideoSpec,
)


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


class FFmpegRenderingTests(unittest.TestCase):
    def _manifest(self, root, *, video=False, subtitle_name="captions.srt"):
        root = Path(root)
        visual = root / ("clip.mp4" if video else "cover.png")
        audio = root / "audio.wav"
        subtitles = root / subtitle_name
        visual.write_bytes(b"visual")
        audio.write_bytes(b"audio")
        subtitles.write_text("captions", encoding="utf-8")
        return VideoComposer().plan(
            visual=visual,
            audio=audio,
            subtitles=subtitles,
            duration_seconds=2.5,
            width=1280,
            height=720,
            fps=25,
        )

    def test_command_is_deterministic_for_image_and_escaped_subtitles(self):
        with tempfile.TemporaryDirectory() as root:
            manifest = self._manifest(root, subtitle_name="captions:hi.srt")
            command = FFmpegCommandBuilder("ffmpeg-custom").build(
                manifest, Path(root) / "out.mp4"
            )
            self.assertEqual(command[0], "ffmpeg-custom")
            self.assertIn("-loop", command)
            self.assertEqual(command[command.index("-t") + 1], "2.500")
            video_filter = command[command.index("-vf") + 1]
            self.assertIn("scale=1280:720", video_filter)
            self.assertIn("captions\\:hi.srt", video_filter)
            self.assertEqual(command[-1], str(Path(root) / "out.mp4"))

    def test_video_input_loops_without_image_loop_flag(self):
        with tempfile.TemporaryDirectory() as root:
            manifest = self._manifest(root, video=True)
            command = FFmpegCommandBuilder().build(manifest, Path(root) / "out.mp4")
            self.assertIn("-stream_loop", command)
            self.assertNotIn("-loop", command)

    def test_renderer_reports_progress_and_atomically_finalizes(self):
        with tempfile.TemporaryDirectory() as root:
            manifest = self._manifest(root)
            output = Path(root) / "final.mp4"
            values = []

            class Process:
                stdout = iter(("out_time_us=1250000\n", "progress=end\n"))
                returncode = 0

                def __init__(self, command, **kwargs):
                    Path(command[-1]).write_bytes(b"rendered")

                def wait(self):
                    return self.returncode

            result = FFmpegRenderer(popen_factory=Process).render(
                manifest, output, progress=values.append
            )
            self.assertEqual(result, output.resolve())
            self.assertEqual(output.read_bytes(), b"rendered")
            self.assertAlmostEqual(values[0], 50.0)
            self.assertEqual(values[-1], 100.0)
            self.assertFalse(Path(root, "final.partial.mp4").exists())

    def test_renderer_cleans_partial_output_on_failure_and_cancel(self):
        with tempfile.TemporaryDirectory() as root:
            manifest = self._manifest(root)
            output = Path(root) / "final.mp4"

            class FailedProcess:
                stdout = iter(("encoder failed\n",))
                returncode = 7

                def __init__(self, command, **kwargs):
                    Path(command[-1]).write_bytes(b"partial")

                def wait(self):
                    return self.returncode

            with self.assertRaisesRegex(FFmpegRenderError, "encoder failed"):
                FFmpegRenderer(popen_factory=FailedProcess).render(manifest, output)
            self.assertFalse(Path(root, "final.partial.mp4").exists())

            cancelled = Event()
            cancelled.set()

            class CancelProcess(FailedProcess):
                stdout = iter(("out_time_us=1000\n",))
                terminated = False

                def terminate(self):
                    self.terminated = True

            with self.assertRaises(RenderCancelled):
                FFmpegRenderer(popen_factory=CancelProcess).render(
                    manifest, output, cancel_event=cancelled
                )
            self.assertFalse(Path(root, "final.partial.mp4").exists())

    def test_progress_parser_ignores_noise_and_clamps(self):
        parser = FFmpegRenderer.progress_from_line
        self.assertIsNone(parser("encoder message", 1000))
        self.assertIsNone(parser("out_time_us=bad", 1000))
        self.assertEqual(parser("out_time_us=2000000", 1000), 100.0)


if __name__ == "__main__":
    unittest.main()
