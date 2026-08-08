from __future__ import annotations

import os
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, QTimer, Signal, Slot
from PySide6.QtWidgets import QApplication

from backend.tts.progress import TTSProgress
from desktop.controllers.tts_controller import TTSController
from desktop.ui.dialogs.tts_progress_dialog import TTSProgressDialog
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


class ThreadWorker(QObject):
    started = Signal()
    progress = Signal(object)
    finished = Signal(object)
    failed = Signal(str)
    cancelled = Signal()
    log = Signal(str)

    def __init__(self, delay_ms=30):
        super().__init__()
        self.delay_ms = delay_ms
        self.was_cancelled = False
        self.config = {}

    def configure(self, **kwargs):
        self.config = kwargs

    @Slot()
    def run(self):
        self.started.emit()
        QTimer.singleShot(self.delay_ms, self._finish)

    def _finish(self):
        if not self.was_cancelled:
            self.finished.emit(SimpleNamespace(output_file="thread-output.wav"))

    def request_cancel(self):
        if not self.was_cancelled:
            self.was_cancelled = True
            self.cancelled.emit()

    def available_speakers(self):
        return []


def wait_until(app, predicate, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        app.processEvents()
        if predicate():
            return True
        time.sleep(0.005)
    app.processEvents()
    return bool(predicate())


class TTSControllerThreadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_real_qthread_completion_cleans_references(self):
        controller = TTSController(worker_factory=lambda: ThreadWorker(20))
        finished = []
        controller.generation_finished.connect(finished.append)
        controller.generate("voice.wav", "reference", "text", "output")
        self.assertTrue(wait_until(self.app, lambda: len(finished) == 1))
        self.assertTrue(wait_until(self.app, lambda: controller.thread is None))
        self.assertFalse(controller.is_running())
        self.assertEqual(controller.output_file(), "thread-output.wav")
        self.assertIsNone(controller.worker)

    def test_real_qthread_cancellation_and_shutdown(self):
        worker = ThreadWorker(500)
        controller = TTSController(worker_factory=lambda: worker)
        cancelled = []
        controller.generation_cancelled.connect(lambda: cancelled.append(True))
        controller.generate("voice.wav", "reference", "text", "output")
        self.assertTrue(wait_until(self.app, controller.is_running))
        controller.cancel()
        self.assertTrue(wait_until(self.app, lambda: bool(cancelled)))
        self.assertTrue(wait_until(self.app, lambda: controller.thread is None))
        self.assertTrue(worker.was_cancelled)
        self.assertTrue(controller.shutdown(wait=True))


class TTSProgressDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_progress_and_window_close_request_cancellation(self):
        controller = FakeTTSController()
        dialog = TTSProgressDialog()
        dialog.set_controller(controller)
        controller.running = True
        controller.generation_started.emit()
        controller.generation_progress.emit(TTSProgress(
            stage="Generating",
            current_chunk=1,
            total_chunks=2,
            current_text="नमस्ते",
            percent=50,
            remaining_seconds=5,
        ))
        self.app.processEvents()
        self.assertEqual(dialog.progress_bar.value(), 50)
        self.assertEqual(dialog.chunk_value.text(), "1 / 2")
        self.assertEqual(dialog.current_text.toPlainText(), "नमस्ते")
        dialog.close()
        self.app.processEvents()
        self.assertTrue(controller.cancelled)
        self.assertFalse(dialog.timer.isActive())


if __name__ == "__main__":
    unittest.main()
