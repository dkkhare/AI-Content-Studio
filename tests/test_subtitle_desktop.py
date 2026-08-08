from __future__ import annotations

import os
import tempfile
import unittest
import wave
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from backend.project.project import Project
from desktop.controllers.subtitle_controller import SubtitleDesktopController
from desktop.ui.widgets.subtitle_panel import SubtitlePanel
from desktop.ui.workspace import Workspace


def write_wav(path, seconds=2, rate=8000):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(rate)
        audio.writeframes(b"\\x00\\x00" * int(seconds * rate))


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


    def test_project_context_duration_text_and_cue_lookup(self):
        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)
            project = Project("Context", root_path).initialize()
            audio = root_path / "output" / "narration.wav"
            text = root_path / "output" / "script.txt"
            write_wav(audio, seconds=2.5)
            text.write_text("परियोजना का कथन", encoding="utf-8")
            project.narration_file = str(audio)
            controller = SubtitleDesktopController()
            controller.set_project(project)
            context = controller.project_context()
            self.assertEqual(context["text"], "परियोजना का कथन")
            self.assertAlmostEqual(context["duration_seconds"], 2.5, places=3)

            document = controller.generate(context["text"], 2.5)
            first = document.cues[0]
            self.assertEqual(controller.cue_at(first.start_ms), first)
            self.assertIsNone(controller.cue_at(document.cues[-1].end_ms))


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


    def test_project_context_populates_duration_and_syncs_preview(self):
        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)
            project = Project("Preview", root_path).initialize()
            audio = root_path / "output" / "narration.wav"
            text = root_path / "output" / "script.txt"
            write_wav(audio, seconds=4)
            text.write_text("पहला वाक्य। दूसरा वाक्य।", encoding="utf-8")
            project.narration_file = str(audio)

            panel = SubtitlePanel()
            panel.set_project(project)
            self.assertEqual(panel.source_text.toPlainText(), text.read_text(encoding="utf-8"))
            self.assertAlmostEqual(panel.duration.value(), 4.0, places=2)
            panel.generate_subtitles()
            cue = panel.controller.document.cues[0]
            panel._position_changed(SimpleNamespace(position=cue.start_ms))
            self.assertEqual(panel.table.currentRow(), 0)
            self.assertEqual(panel.preview_text.text(), cue.text)
            self.assertGreater(panel.timeline.maximum(), 0)
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
