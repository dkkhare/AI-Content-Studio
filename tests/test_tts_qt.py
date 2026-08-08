from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from desktop.ui.widgets.narration_panel import NarrationPanel
from desktop.ui.workspace import Workspace


class FakeTTSController(QObject):
    generation_started = Signal()
    generation_progress = Signal(object)
    generation_finished = Signal(object)
    generation_failed = Signal(str)
    generation_cancelled = Signal()
    log_message = Signal(str)

    def __init__(self):
        super().__init__()
        self.running = False
        self.calls = []
        self.cancelled = False
        self.cleaned = False

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        self.running = True
        self.generation_started.emit()

    def is_running(self):
        return self.running

    def cancel(self):
        self.running = False
        self.cancelled = True
        self.generation_cancelled.emit()

    def available_speakers(self):
        return ["Hindi Voice"]

    def session(self):
        return None

    def statistics(self):
        return {"running": self.running}

    def cleanup(self):
        self.cleaned = True
        self.running = False


class NarrationPanelQtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_workspace_uses_real_narration_panel(self):
        workspace = Workspace()
        try:
            self.assertIsInstance(workspace.narration_panel, NarrationPanel)
            self.assertEqual(workspace.current_tab_name(), "PDF")
            workspace.open_narration_tab()
            self.assertEqual(workspace.current_tab_name(), "Narration")
        finally:
            workspace.narration_panel.cleanup()
            workspace.close()

    def test_generate_finish_cancel_and_state_round_trip(self):
        controller = FakeTTSController()
        panel = NarrationPanel(controller=controller)
        with tempfile.TemporaryDirectory() as root:
            reference = Path(root) / "voice.wav"
            reference.write_bytes(b"RIFF")
            panel.set_reference_audio(str(reference))
            panel.reference_text.setPlainText("reference words")
            panel.narration_text.setPlainText("नमस्ते दुनिया")
            panel.output_directory = str(Path(root) / "output")

            self.assertTrue(panel.validate_inputs(show_message=False))
            panel.generate_narration()
            self.assertEqual(len(controller.calls), 1)
            self.assertEqual(controller.calls[0]["voice_name"], "Hindi Voice")
            self.assertFalse(panel.generate_button.isEnabled())
            self.assertTrue(panel.cancel_button.isEnabled())

            output = str(Path(root) / "output" / "narration.wav")
            controller.running = False
            controller.generation_finished.emit(SimpleNamespace(output_file=output))
            self.assertEqual(panel.recent_outputs(), [output])
            self.assertTrue(panel.generate_button.isEnabled())
            self.assertFalse(panel.cancel_button.isEnabled())

            state = panel.save_state()
            restored = NarrationPanel(controller=FakeTTSController())
            restored.restore_state(state)
            self.assertEqual(restored.reference_audio, str(reference))
            self.assertEqual(restored.narration_text.toPlainText(), "नमस्ते दुनिया")
            restored.cleanup()

            controller.running = True
            panel.refresh()
            panel.cancel_generation()
            self.assertTrue(controller.cancelled)
        panel.cleanup()
        self.assertTrue(controller.cleaned)


if __name__ == "__main__":
    unittest.main()
