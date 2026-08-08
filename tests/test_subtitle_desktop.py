from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from backend.project.project import Project
from desktop.controllers.subtitle_controller import SubtitleDesktopController
from desktop.ui.widgets.subtitle_panel import SubtitlePanel
from desktop.ui.workspace import Workspace


class SubtitleDesktopControllerTests(unittest.TestCase):
    def test_generate_edit_export_and_project_reload(self):
        with tempfile.TemporaryDirectory() as root:
            project = Project("Desktop Subtitle", Path(root)).initialize()
            controller = SubtitleDesktopController()
            controller.set_project(project)
            document = controller.generate(
                "यह पहला वाक्य है। यह दूसरा वाक्य है।",
                6,
                format="srt",
            )
            self.assertGreaterEqual(len(document.cues), 1)
            self.assertTrue(Path(project.subtitle_file).is_file())

            rows = controller.cue_rows()
            rows[0]["text"] = "संपादित पाठ"
            edited = controller.replace_cues(rows)
            self.assertEqual(edited.cues[0].text, "संपादित पाठ")

            exported = controller.export_file(Path(root) / "copy.vtt")
            self.assertTrue(exported.is_file())

            reloaded = SubtitleDesktopController()
            loaded = reloaded.set_project(project)
            self.assertGreaterEqual(len(loaded.cues), 1)


class SubtitlePanelQtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_panel_generates_and_applies_table_edits(self):
        with tempfile.TemporaryDirectory() as root:
            project = Project("Subtitle UI", Path(root)).initialize()
            panel = SubtitlePanel()
            panel.set_project(project)
            panel.source_text.setPlainText("पहला वाक्य। दूसरा वाक्य।")
            panel.duration.setValue(5)
            panel.generate_subtitles()
            self.assertGreater(panel.table.rowCount(), 0)
            self.assertTrue(panel.export_button.isEnabled())

            panel.table.item(0, 3).setText("बदला हुआ पाठ")
            panel.apply_edits()
            self.assertEqual(
                panel.controller.document.cues[0].text,
                "बदला हुआ पाठ",
            )
            self.assertIn("Applied edits", panel.status.text())
            panel.dispose()

    def test_workspace_exposes_subtitle_tab_in_pipeline_order(self):
        workspace = Workspace()
        try:
            self.assertEqual(workspace.tab_count(), 7)
            workspace.open_subtitle_tab()
            self.assertEqual(workspace.current_tab_name(), "Subtitles")
            self.assertIsInstance(workspace.subtitle_panel, SubtitlePanel)
        finally:
            workspace.dispose()
            workspace.close()


if __name__ == "__main__":
    unittest.main()
