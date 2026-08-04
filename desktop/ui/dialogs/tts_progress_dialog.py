from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import (
    Qt,
    QTimer,
)

from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QProgressBar,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
)


class TTSProgressDialog(QDialog):
    """
    Progress dialog displayed while narration is generated.
    """

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setWindowTitle(
            "Generating Narration"
        )

        self.resize(700, 520)

        self.setModal(True)

        self.start_time = None

        self.controller = None

        self._build_ui()

        self._create_timer()
    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def _build_ui(self):

        layout = QVBoxLayout(self)

        # ------------------------------------------
        # Status
        # ------------------------------------------

        self.status_label = QLabel(
            "Preparing..."
        )

        layout.addWidget(
            self.status_label
        )

        # ------------------------------------------
        # Progress Bar
        # ------------------------------------------

        self.progress_bar = QProgressBar()

        self.progress_bar.setRange(
            0,
            100,
        )

        self.progress_bar.setValue(0)

        layout.addWidget(
            self.progress_bar
        )

        # ------------------------------------------
        # Information
        # ------------------------------------------

        info_group = QGroupBox(
            "Generation Status"
        )

        grid = QGridLayout(
            info_group
        )

        grid.addWidget(
            QLabel("Stage:"),
            0,
            0,
        )

        self.stage_value = QLabel("-")

        grid.addWidget(
            self.stage_value,
            0,
            1,
        )

        grid.addWidget(
            QLabel("Chunk:"),
            1,
            0,
        )

        self.chunk_value = QLabel(
            "0 / 0"
        )

        grid.addWidget(
            self.chunk_value,
            1,
            1,
        )

        grid.addWidget(
            QLabel("Elapsed:"),
            2,
            0,
        )

        self.elapsed_value = QLabel(
            "00:00"
        )

        grid.addWidget(
            self.elapsed_value,
            2,
            1,
        )

        grid.addWidget(
            QLabel("Remaining:"),
            3,
            0,
        )

        self.remaining_value = QLabel(
            "--:--"
        )

        grid.addWidget(
            self.remaining_value,
            3,
            1,
        )

        layout.addWidget(
            info_group
        )

        # ------------------------------------------
        # Current Text
        # ------------------------------------------

        current_group = QGroupBox(
            "Current Text"
        )

        current_layout = QVBoxLayout(
            current_group
        )

        self.current_text = QTextEdit()

        self.current_text.setReadOnly(
            True
        )

        current_layout.addWidget(
            self.current_text
        )

        layout.addWidget(
            current_group
        )

        # ------------------------------------------
        # Log
        # ------------------------------------------

        log_group = QGroupBox(
            "Generation Log"
        )

        log_layout = QVBoxLayout(
            log_group
        )

        self.log_view = QTextEdit()

        self.log_view.setReadOnly(
            True
        )

        log_layout.addWidget(
            self.log_view
        )

        layout.addWidget(
            log_group
        )

        # ------------------------------------------
        # Buttons
        # ------------------------------------------

        button_layout = QHBoxLayout()

        button_layout.addStretch()

        self.cancel_button = QPushButton(
            "Cancel"
        )

        button_layout.addWidget(
            self.cancel_button
        )

        layout.addLayout(
            button_layout
        )
    # --------------------------------------------------
    # Timer
    # --------------------------------------------------

    def _create_timer(self):

        self.timer = QTimer(self)

        self.timer.setInterval(
            1000
        )

    # --------------------------------------------------

    def start_timer(self):

        self.start_time = datetime.now()

        self.timer.start()

    # --------------------------------------------------

    def stop_timer(self):

        self.timer.stop()