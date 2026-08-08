from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from desktop.controllers.tts_controller import TTSController
from desktop.ui.dialogs.tts_progress_dialog import TTSProgressDialog


class NarrationPanel(QWidget):
    """Reference-voice narration workbench backed by TTSController."""

    narration_started = Signal()
    narration_finished = Signal(str)
    narration_failed = Signal(str)
    AUDIO_SUFFIXES = {".wav", ".mp3", ".flac", ".ogg"}

    def __init__(self, parent=None, *, controller=None):
        super().__init__(parent)
        self.controller = controller or TTSController(self)
        self.progress_dialog = None
        self.reference_audio = ""
        self.output_directory = "output/tts"
        self._recent_outputs = []
        self._build_ui()
        self._connect_controller()
        self.setAcceptDrops(True)
        self.refresh_voice_profiles()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)
        title = QLabel("AI Narration")
        title.setObjectName("title")
        root.addWidget(title)

        voice_group = QGroupBox("Reference Voice")
        voice_form = QFormLayout(voice_group)
        audio_row = QHBoxLayout()
        self.reference_audio_edit = QLineEdit()
        self.reference_audio_edit.setReadOnly(True)
        self.browse_button = QPushButton("Browse...")
        audio_row.addWidget(self.reference_audio_edit)
        audio_row.addWidget(self.browse_button)
        voice_form.addRow("Reference audio", audio_row)
        self.voice_combo = QComboBox()
        voice_form.addRow("Voice profile", self.voice_combo)
        root.addWidget(voice_group)

        text_group = QGroupBox("Narration Text")
        text_layout = QFormLayout(text_group)
        self.reference_text = QTextEdit()
        self.reference_text.setPlaceholderText("Reference transcript...")
        self.reference_text.setMinimumHeight(90)
        self.narration_text = QTextEdit()
        self.narration_text.setPlaceholderText("Enter narration text...")
        self.narration_text.setMinimumHeight(220)
        text_layout.addRow("Reference transcript", self.reference_text)
        text_layout.addRow("Narration", self.narration_text)
        root.addWidget(text_group)

        actions = QHBoxLayout()
        actions.addStretch()
        self.generate_button = QPushButton("Generate Narration")
        self.cancel_button = QPushButton("Cancel")
        actions.addWidget(self.generate_button)
        actions.addWidget(self.cancel_button)
        root.addLayout(actions)

    def _connect_controller(self):
        self.browse_button.clicked.connect(self.browse_reference_audio)
        self.generate_button.clicked.connect(self.generate_narration)
        self.cancel_button.clicked.connect(self.cancel_generation)
        self.controller.generation_started.connect(self._generation_started)
        self.controller.generation_progress.connect(self._update_progress)
        self.controller.generation_finished.connect(self._generation_finished)
        self.controller.generation_failed.connect(self._generation_failed)
        self.controller.generation_cancelled.connect(self._generation_cancelled)

    def browse_reference_audio(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select Reference Audio", "", "Audio Files (*.wav *.mp3 *.flac *.ogg)"
        )
        if filename:
            self.set_reference_audio(filename)

    def set_reference_audio(self, filename):
        self.reference_audio = str(filename)
        self.reference_audio_edit.setText(self.reference_audio)

    def validation_error(self):
        if not self.reference_audio:
            return "Please select a reference audio file."
        if not Path(self.reference_audio).is_file():
            return "Reference audio file does not exist."
        if Path(self.reference_audio).suffix.lower() not in self.AUDIO_SUFFIXES:
            return "Unsupported reference audio format."
        if not self.reference_text.toPlainText().strip():
            return "Reference transcript is required."
        if not self.narration_text.toPlainText().strip():
            return "Narration text is required."
        return ""

    def validate_inputs(self, *, show_message=True):
        message = self.validation_error()
        if message and show_message:
            QMessageBox.warning(self, "Narration", message)
        return not message

    def _create_progress_dialog(self):
        self.progress_dialog = TTSProgressDialog(self)
        self.progress_dialog.set_controller(self.controller)

    def generate_narration(self):
        if not self.validate_inputs():
            return
        if self.controller.is_running():
            QMessageBox.information(self, "Narration", "Generation is already running.")
            return
        self._create_progress_dialog()
        try:
            self.controller.generate(
                reference_audio=self.reference_audio,
                reference_text=self.reference_text.toPlainText(),
                text=self.narration_text.toPlainText(),
                output_directory=self.output_directory,
                voice_name=self.selected_voice(),
            )
        except Exception as exc:
            self.progress_dialog.deleteLater()
            self.progress_dialog = None
            QMessageBox.critical(self, "Narration Error", str(exc))
            return
        self.progress_dialog.show()

    def cancel_generation(self):
        if self.controller.is_running():
            self.controller.cancel()

    def _generation_started(self):
        self.refresh()
        self.narration_started.emit()

    def _update_progress(self, progress):
        if self.progress_dialog and not hasattr(self.progress_dialog, "on_progress"):
            self.progress_dialog.update_progress(progress)

    def _close_progress(self):
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

    def _generation_finished(self, session):
        self.refresh()
        self._close_progress()
        output = getattr(session, "output_file", "") if session else ""
        if output:
            self.add_recent_output(output)
            self.narration_finished.emit(output)
        self.refresh_voice_profiles()

    def _generation_failed(self, message):
        self.refresh()
        self._close_progress()
        self.narration_failed.emit(str(message))

    def _generation_cancelled(self):
        self.refresh()
        self._close_progress()

    def load_voice_profiles(self, profiles):
        selected = self.selected_voice()
        self.voice_combo.clear()
        self.voice_combo.addItems([str(item) for item in profiles])
        index = self.voice_combo.findText(selected)
        if index >= 0:
            self.voice_combo.setCurrentIndex(index)

    def selected_voice(self):
        return self.voice_combo.currentText()

    def refresh_voice_profiles(self):
        try:
            self.load_voice_profiles(self.controller.available_speakers())
        except Exception:
            self.load_voice_profiles([])

    def add_recent_output(self, filename):
        value = str(filename)
        if not value:
            return
        if value in self._recent_outputs:
            self._recent_outputs.remove(value)
        self._recent_outputs.insert(0, value)
        del self._recent_outputs[10:]

    def recent_outputs(self):
        return list(self._recent_outputs)

    def clear_recent_outputs(self):
        self._recent_outputs.clear()

    def save_state(self):
        return {
            "reference_audio": self.reference_audio,
            "reference_text": self.reference_text.toPlainText(),
            "narration": self.narration_text.toPlainText(),
            "voice": self.selected_voice(),
            "output_directory": self.output_directory,
            "recent_outputs": self.recent_outputs(),
        }

    def restore_state(self, state):
        if not state:
            return
        self.set_reference_audio(state.get("reference_audio", ""))
        self.reference_text.setPlainText(state.get("reference_text", ""))
        self.narration_text.setPlainText(state.get("narration", ""))
        self.output_directory = str(state.get("output_directory", self.output_directory))
        self._recent_outputs = list(state.get("recent_outputs", []))[:10]
        voice = str(state.get("voice", ""))
        index = self.voice_combo.findText(voice)
        if index >= 0:
            self.voice_combo.setCurrentIndex(index)

    def clear(self):
        self.set_reference_audio("")
        self.reference_text.clear()
        self.narration_text.clear()
        self.voice_combo.setCurrentIndex(-1)

    def refresh(self):
        running = self.controller.is_running()
        self.generate_button.setEnabled(not running)
        self.cancel_button.setEnabled(running)

    def is_generating(self):
        return self.controller.is_running()

    def current_session(self):
        return self.controller.session()

    def statistics(self):
        return self.controller.statistics()

    def cleanup(self):
        self.controller.cleanup()

    def dragEnterEvent(self, event):
        urls = event.mimeData().urls() if event.mimeData().hasUrls() else []
        if urls and Path(urls[0].toLocalFile()).suffix.lower() in self.AUDIO_SUFFIXES:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            filename = urls[0].toLocalFile()
            if Path(filename).suffix.lower() in self.AUDIO_SUFFIXES:
                self.set_reference_audio(filename)
                event.acceptProposedAction()

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Return:
            self.generate_narration()
            return
        if event.key() == Qt.Key_Escape:
            self.cancel_generation()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        self.cleanup()
        event.accept()

    def debug_info(self):
        return {
            "reference_audio": self.reference_audio,
            "output_directory": self.output_directory,
            "running": self.is_generating(),
            "recent_outputs": len(self._recent_outputs),
        }
