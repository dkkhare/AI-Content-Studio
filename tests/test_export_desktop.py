from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from backend.project.project import Project
from desktop.controllers.export_controller import ExportDesktopController
from desktop.ui.widgets.export_panel import ExportPanel
from desktop.ui.workspace import Workspace


def make_project(root):
    root = Path(root)
    project = Project("Hindi Publishing", root).initialize()
    video = root / "output" / "video.mp4"
    subtitles = root / "output" / "subtitles.srt"
    cover = root / "cover.png"
    video.write_bytes(b"video")
    subtitles.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nनमस्ते\n",
        encoding="utf-8",
    )
    cover.write_bytes(b"cover")
    project.video_file = str(video)
    project.subtitle_file = str(subtitles)
    project.cover_image = str(cover)
    return project


class ExportDesktopControllerTests(unittest.TestCase):
    def test_context_preview_default_destination_and_sync_export(self):
        with tempfile.TemporaryDirectory() as root:
            project = make_project(root)
            controller = ExportDesktopController()
            context = controller.set_project(project)
            self.assertEqual(context["presets"], ("archive", "publishing", "video"))
            self.assertTrue(
                context["destination"].endswith("hindi-publishing-publishing")
            )
            preview = controller.preview("publishing")
            self.assertEqual(
                {item["role"] for item in preview},
                {"video_file", "subtitle_file", "cover_image"},
            )
            destination = Path(root) / "package"
            values = []
            manifest, output = controller.export_sync(
                destination, "publishing", progress=values.append
            )
            self.assertEqual(output, destination.resolve())
            self.assertEqual(len(manifest.assets), 3)
            self.assertEqual(values[-1], 100.0)

    def test_controller_requires_project(self):
        controller = ExportDesktopController()
        with self.assertRaises(RuntimeError):
            controller.preview()
        with self.assertRaises(RuntimeError):
            controller.export_sync("package")


class ExportPanelQtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_panel_populates_presets_preview_and_destination(self):
        with tempfile.TemporaryDirectory() as root:
            project = make_project(root)
            panel = ExportPanel()
            panel.set_project(project)
            self.assertEqual(panel.preset.currentText(), "publishing")
            self.assertEqual(panel.preview.rowCount(), 3)
            self.assertIn("hindi-publishing-publishing", panel.destination.text())
            self.assertEqual(panel.validation_error(), "")
            self.assertTrue(panel.export_button.isEnabled())
            panel.dispose()

    def test_workspace_replaces_export_placeholder_and_propagates_project(self):
        with tempfile.TemporaryDirectory() as root:
            project = make_project(root)
            workspace = Workspace()
            try:
                self.assertIsInstance(workspace.export_page, ExportPanel)
                workspace.open_project(project)
                workspace.open_export_tab()
                self.assertEqual(workspace.current_tab_name(), "Export")
                self.assertIs(workspace.export_page.controller.project, project)
                self.assertGreater(workspace.export_page.preview.rowCount(), 0)
            finally:
                workspace.dispose()
                workspace.close()


if __name__ == "__main__":
    unittest.main()
