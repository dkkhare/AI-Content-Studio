from __future__ import annotations

import os
import tempfile
import unittest
import wave
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from backend.project.project import Project
from desktop.controllers.video_controller import VideoDesktopController
from desktop.ui.widgets.video_panel import VideoPanel
from desktop.ui.workspace import Workspace


def write_wav(path, seconds=2, rate=8000):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(rate)
        audio.writeframes(b"\x00\x00" * int(seconds * rate))


class FakeRenderer:
    def __init__(self):
        self.calls = []

    def render(self, manifest, output, progress=None, cancel_event=None):
        target = Path(output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"video")
        self.calls.append((manifest, target))
        if progress:
            progress(100.0)
        return target


class VideoDesktopControllerTests(unittest.TestCase):
    def _project(self, root, seconds=3):
        root = Path(root)
        project = Project("Video Desktop", root).initialize()
        image = root / "cover.png"
        audio = root / "output" / "narration.wav"
        subtitles = root / "output" / "subtitles.srt"
        image.write_bytes(b"image")
        write_wav(audio, seconds=seconds)
        subtitles.write_text(
            "1\n00:00:00,000 --> 00:00:01,000\nनमस्ते\n",
            encoding="utf-8",
        )
        project.cover_image = str(image)
        project.narration_file = str(audio)
        project.subtitle_file = str(subtitles)
        return project

    def test_context_discovers_assets_and_audio_duration(self):
        with tempfile.TemporaryDirectory() as root:
            project = self._project(root, seconds=2.5)
            controller = VideoDesktopController(renderer=FakeRenderer())
            context = controller.set_project(project)
            self.assertEqual(context["visual"], project.cover_image)
            self.assertEqual(context["audio"], project.narration_file)
            self.assertEqual(context["subtitles"], project.subtitle_file)
            self.assertAlmostEqual(context["duration_seconds"], 2.5, places=3)
            self.assertTrue(context["output"].endswith("output/video.mp4"))

    def test_sync_render_registers_project_video_and_rejects_escape(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as outside:
            project = self._project(root)
            renderer = FakeRenderer()
            controller = VideoDesktopController(renderer=renderer)
            context = controller.set_project(project)
            output = controller.render_sync(
                visual=context["visual"],
                audio=context["audio"],
                subtitles=context["subtitles"],
                duration_seconds=context["duration_seconds"],
                width=1280,
                height=720,
                fps=25,
            )
            self.assertTrue(Path(output).is_file())
            self.assertEqual(project.video_file, output)
            self.assertEqual(project.status, "completed")
            self.assertEqual(project.progress, 100)
            with self.assertRaises(ValueError):
                controller.prepare(
                    visual=context["visual"],
                    audio=context["audio"],
                    duration_seconds=3,
                    output=str(Path(outside) / "video.mp4"),
                )


class VideoPanelQtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_panel_populates_project_assets_and_settings(self):
        with tempfile.TemporaryDirectory() as root:
            project = VideoDesktopControllerTests()._project(root, seconds=4)
            panel = VideoPanel(controller=VideoDesktopController(renderer=FakeRenderer()))
            panel.set_project(project)
            self.assertEqual(panel.visual.text(), project.cover_image)
            self.assertEqual(panel.audio.text(), project.narration_file)
            self.assertEqual(panel.subtitles.text(), project.subtitle_file)
            self.assertAlmostEqual(panel.duration.value(), 4.0, places=2)
            self.assertEqual(panel.validation_error(), "")
            settings = panel.settings()
            self.assertEqual((settings["width"], settings["height"]), (1920, 1080))
            panel.dispose()

    def test_workspace_replaces_video_placeholder_and_propagates_project(self):
        with tempfile.TemporaryDirectory() as root:
            project = VideoDesktopControllerTests()._project(root)
            workspace = Workspace()
            try:
                self.assertIsInstance(workspace.video_page, VideoPanel)
                workspace.open_project(project)
                workspace.open_video_tab()
                self.assertEqual(workspace.current_tab_name(), "Video")
                self.assertIs(workspace.video_page.controller.project, project)
            finally:
                workspace.dispose()
                workspace.close()


if __name__ == "__main__":
    unittest.main()
