from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QTextEdit,
    QLineEdit,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QComboBox,
    QSizePolicy,
    QMessageBox,
)

from desktop.controllers.tts_controller import TTSController
from desktop.ui.dialogs.tts_progress_dialog import (
    TTSProgressDialog,
)


class NarrationPanel(QWidget):
    """
    Narration generation panel.

    Provides:

    • Reference audio selection
    • Reference transcript
    • Narration editor
    • Voice profile selection
    • Generate narration
    • Progress dialog integration
    """

    narration_started = Signal()

    narration_finished = Signal(str)

    narration_failed = Signal(str)

    def __init__(self, parent=None):

        super().__init__(parent)

        self.controller = TTSController(self)

        self.progress_dialog = None

        self.reference_audio = ""

        self.output_directory = "output/tts"

        self._build_ui()

        self._connect_controller()
    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def _build_ui(self):

        root = QVBoxLayout(self)

        root.setSpacing(12)

        root.setContentsMargins(12, 12, 12, 12)

        title = QLabel("AI Narration")

        title.setObjectName("title")

        root.addWidget(title)

        self._create_reference_group(root)

        self._create_text_group(root)

        self._create_button_bar(root)

        root.addStretch()

    # --------------------------------------------------
    # Reference Group
    # --------------------------------------------------

    def _create_reference_group(self, layout):

        group = QGroupBox("Reference Voice")

        grid = QGridLayout(group)

        grid.addWidget(
            QLabel("Reference Audio"),
            0,
            0,
        )

        self.reference_audio_edit = QLineEdit()

        self.reference_audio_edit.setReadOnly(True)

        grid.addWidget(
            self.reference_audio_edit,
            0,
            1,
        )

        self.browse_button = QPushButton(
            "Browse..."
        )

        grid.addWidget(
            self.browse_button,
            0,
            2,
        )

        grid.addWidget(
            QLabel("Voice Profile"),
            1,
            0,
        )

        self.voice_combo = QComboBox()

        self.voice_combo.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        grid.addWidget(
            self.voice_combo,
            1,
            1,
            1,
            2,
        )

        layout.addWidget(group)

    # --------------------------------------------------
    # Narration Text
    # --------------------------------------------------

    def _create_text_group(self, layout):

        group = QGroupBox(
            "Narration Text"
        )

        box = QVBoxLayout(group)

        self.reference_text = QTextEdit()

        self.reference_text.setPlaceholderText(
            "Reference transcript..."
        )

        self.reference_text.setMinimumHeight(
            100
        )

        box.addWidget(
            QLabel(
                "Reference Transcript"
            )
        )

        box.addWidget(
            self.reference_text
        )

        self.narration_text = QTextEdit()

        self.narration_text.setPlaceholderText(
            "Enter narration text..."
        )

        self.narration_text.setMinimumHeight(
            250
        )

        box.addWidget(
            QLabel("Narration")
        )

        box.addWidget(
            self.narration_text
        )

        layout.addWidget(group)
    # --------------------------------------------------
    # Buttons
    # --------------------------------------------------

    def _create_button_bar(self, layout):

        row = QHBoxLayout()

        self.generate_button = QPushButton(
            "Generate Narration"
        )

        self.cancel_button = QPushButton(
            "Cancel"
        )

        self.cancel_button.setEnabled(False)

        row.addStretch()

        row.addWidget(
            self.generate_button
        )

        row.addWidget(
            self.cancel_button
        )

        layout.addLayout(row)
    # --------------------------------------------------
    # Connections
    # --------------------------------------------------

    def _connect_controller(self):

        self.browse_button.clicked.connect(
            self.browse_reference_audio
        )

        self.generate_button.clicked.connect(
            self.generate_narration
        )

        self.cancel_button.clicked.connect(
            self.cancel_generation
        )

        self.controller.generation_started.connect(
            self._generation_started
        )

        self.controller.generation_finished.connect(
            self._generation_finished
        )

        self.controller.generation_failed.connect(
            self._generation_failed
        )

        self.controller.generation_cancelled.connect(
            self._generation_cancelled
        )

    # --------------------------------------------------
    # Browse Reference Audio
    # --------------------------------------------------

    def browse_reference_audio(self):

        filename, _ = QFileDialog.getOpenFileName(

            self,

            "Select Reference Audio",

            "",

            "Audio Files (*.wav *.mp3 *.flac)"

        )

        if not filename:

            return

        self.reference_audio = filename

        self.reference_audio_edit.setText(
            filename
        )

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------

    def validate_inputs(self):

        if not self.reference_audio:

            QMessageBox.warning(

                self,

                "Reference Audio",

                "Please select a reference audio."

            )

            return False

        if not Path(
            self.reference_audio
        ).exists():

            QMessageBox.warning(

                self,

                "Reference Audio",

                "Selected reference audio does not exist."

            )

            return False

        if not self.reference_text.toPlainText().strip():

            QMessageBox.warning(

                self,

                "Reference Text",

                "Reference transcript cannot be empty."

            )

            return False

        if not self.narration_text.toPlainText().strip():

            QMessageBox.warning(

                self,

                "Narration",

                "Narration text cannot be empty."

            )

            return False

        return True

    # --------------------------------------------------
    # Progress Dialog
    # --------------------------------------------------

    def _create_progress_dialog(self):

        self.progress_dialog = TTSProgressDialog(
            self
        )

        self.progress_dialog.set_controller(
            self.controller
        )

    # --------------------------------------------------
    # Generate
    # --------------------------------------------------

    def generate_narration(self):

        if not self.validate_inputs():

            return

        if self.controller.is_running():

            QMessageBox.information(

                self,

                "Narration",

                "Narration generation is already running."

            )

            return

        self._create_progress_dialog()

        self.controller.generate(

            reference_audio=self.reference_audio,

            reference_text=self.reference_text.toPlainText(),

            text=self.narration_text.toPlainText(),

            output_directory=self.output_directory,

        )

        self.progress_dialog.show()

    # --------------------------------------------------
    # Cancel
    # --------------------------------------------------

    def cancel_generation(self):

        if self.controller.is_running():

            self.controller.cancel()
    # --------------------------------------------------
    # Controller Events
    # --------------------------------------------------

    def _generation_started(self):

        self.generate_button.setEnabled(False)

        self.cancel_button.setEnabled(True)

        self.narration_started.emit()

    # --------------------------------------------------

def _generation_finished(self, session):

    self.generate_button.setEnabled(True)

    self.cancel_button.setEnabled(False)

    if session:

        self.add_recent_output(
            session.output_file
        )

        self.refresh_voice_profiles()

        self.narration_finished.emit(
            session.output_file
        )
    # --------------------------------------------------

    def _generation_failed(self, message):

        self.generate_button.setEnabled(True)

        self.cancel_button.setEnabled(False)

        QMessageBox.critical(

            self,

            "Narration Failed",

            message,

        )

        self.narration_failed.emit(message)

    # --------------------------------------------------

    def _generation_cancelled(self):

        self.generate_button.setEnabled(True)

        self.cancel_button.setEnabled(False)

        QMessageBox.information(

            self,

            "Narration",

            "Narration generation cancelled."

        )
    # --------------------------------------------------
    # Voice Profiles
    # --------------------------------------------------

    def load_voice_profiles(self, profiles):

        self.voice_combo.clear()

        for profile in profiles:

            self.voice_combo.addItem(profile)

    # --------------------------------------------------

    def selected_voice(self):

        return self.voice_combo.currentText()

    # --------------------------------------------------
    # Output Directory
    # --------------------------------------------------

    def set_output_directory(
        self,
        directory,
    ):

        self.output_directory = directory

    def output_path(self):

        return self.output_directory
    # --------------------------------------------------
    # Playback
    # --------------------------------------------------

    def play_output(self):

        output = self.controller.output_file()

        if not output:

            QMessageBox.information(

                self,

                "Playback",

                "No generated narration available."

            )

            return

        if not Path(output).exists():

            QMessageBox.warning(

                self,

                "Playback",

                "Generated audio file not found."

            )

            return

        try:

            from backend.audio.player import AudioPlayer

        except ImportError:

            QMessageBox.warning(

                self,

                "Playback",

                "AudioPlayer is not available."

            )

            return

        if not hasattr(self, "_audio_player"):

            self._audio_player = AudioPlayer()

        self._audio_player.play(output)

    # --------------------------------------------------

    def stop_playback(self):

        if hasattr(self, "_audio_player"):

            self._audio_player.stop()

    # --------------------------------------------------
    # Output Folder
    # --------------------------------------------------

    def open_output_folder(self):

        directory = Path(self.output_directory)

        directory.mkdir(

            parents=True,

            exist_ok=True,

        )

        try:

            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl

            QDesktopServices.openUrl(

                QUrl.fromLocalFile(

                    str(directory)

                )

            )

        except Exception as exc:

            QMessageBox.warning(

                self,

                "Output Folder",

                str(exc),

            )
    # --------------------------------------------------
    # Recent Outputs
    # --------------------------------------------------

    def add_recent_output(

        self,

        filename,

    ):

        if not hasattr(

            self,

            "_recent_outputs",

        ):

            self._recent_outputs = []

        if filename in self._recent_outputs:

            self._recent_outputs.remove(

                filename

            )

        self._recent_outputs.insert(

            0,

            filename,

        )

        self._recent_outputs = (

            self._recent_outputs[:10]

        )

    def recent_outputs(self):

        if not hasattr(

            self,

            "_recent_outputs",

        ):

            self._recent_outputs = []

        return list(

            self._recent_outputs

        )
    # --------------------------------------------------
    # Voice Profiles
    # --------------------------------------------------

    def refresh_voice_profiles(self):

        manager = getattr(

            self.controller,

            "manager",

            None,

        )

        self.voice_combo.clear()

        if manager is None:

            return

        try:

            profiles = (

                manager.available_speakers()

            )

        except Exception:

            profiles = []

        for profile in profiles:

            self.voice_combo.addItem(

                profile

            )

    def selected_voice_profile(self):

        return self.voice_combo.currentText()

    def apply_selected_profile(self):

        profile = (

            self.selected_voice_profile()

        )

        if not profile:

            return

        manager = getattr(

            self.controller,

            "manager",

            None,

        )

        if manager is None:

            return

        try:

            manager.load_speaker(profile)

        except Exception as exc:

            QMessageBox.warning(

                self,

                "Voice Profile",

                str(exc),

            )
