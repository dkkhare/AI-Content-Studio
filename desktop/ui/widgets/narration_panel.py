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