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
    # --------------------------------------------------
    # Controller
    # --------------------------------------------------

    def set_controller(self, controller):

        self.controller = controller

        self.cancel_button.clicked.connect(
            controller.cancel
        )

        self.timer.timeout.connect(
            self._update_elapsed
        )

        controller.generation_started.connect(
            self.on_started
        )

        controller.generation_progress.connect(
            self.on_progress
        )

        controller.generation_finished.connect(
            self.on_finished
        )

        controller.generation_failed.connect(
            self.on_failed
        )

        controller.generation_cancelled.connect(
            self.on_cancelled
        )

        controller.log_message.connect(
            self.append_log
        )

    # --------------------------------------------------
    # Elapsed Timer
    # --------------------------------------------------

    def _update_elapsed(self):

        if self.start_time is None:

            return

        elapsed = datetime.now() - self.start_time

        seconds = int(
            elapsed.total_seconds()
        )

        minutes = seconds // 60

        seconds = seconds % 60

        self.elapsed_value.setText(

            f"{minutes:02}:{seconds:02}"

        )

    # --------------------------------------------------
    # Log
    # --------------------------------------------------

    def append_log(self, message):

        self.log_view.append(message)

    # --------------------------------------------------
    # Started
    # --------------------------------------------------

    def on_started(self):

        self.status_label.setText(
            "Generating narration..."
        )

        self.progress_bar.setValue(0)

        self.start_timer()

    # --------------------------------------------------
    # Progress
    # --------------------------------------------------

    def on_progress(self, progress):

        self.progress_bar.setValue(

            progress.percent

        )

        self.stage_value.setText(

            progress.stage

        )

        self.chunk_value.setText(

            f"{progress.current_chunk} / "

            f"{progress.total_chunks}"

        )

        self.current_text.setPlainText(

            progress.current_text

        )

        if progress.remaining_seconds:

            remaining = int(
                progress.remaining_seconds
            )

            m = remaining // 60

            s = remaining % 60

            self.remaining_value.setText(

                f"{m:02}:{s:02}"

            )

    # --------------------------------------------------
    # Finished
    # --------------------------------------------------

    def on_finished(self, session):

        self.stop_timer()

        self.progress_bar.setValue(100)

        self.status_label.setText(
            "Narration generated successfully."
        )

        self.append_log(
            "Generation completed."
        )

        self.cancel_button.setText(
            "Close"
        )

        try:

            self.cancel_button.clicked.disconnect()

        except Exception:

            pass

        self.cancel_button.clicked.connect(
            self.accept
        )

    # --------------------------------------------------
    # Failed
    # --------------------------------------------------

    def on_failed(self, message):

        self.stop_timer()

        self.status_label.setText(
            "Generation failed."
        )

        self.append_log(message)

        self.cancel_button.setText(
            "Close"
        )

        try:

            self.cancel_button.clicked.disconnect()

        except Exception:

            pass

        self.cancel_button.clicked.connect(
            self.reject
        )

    # --------------------------------------------------
    # Cancelled
    # --------------------------------------------------

    def on_cancelled(self):

        self.stop_timer()

        self.status_label.setText(
            "Generation cancelled."
        )

        self.append_log(
            "Operation cancelled."
        )

        self.cancel_button.setText(
            "Close"
        )

        try:

            self.cancel_button.clicked.disconnect()

        except Exception:

            pass

        self.cancel_button.clicked.connect(
            self.reject
        )

    # --------------------------------------------------
    # Reset
    # --------------------------------------------------

    def reset(self):

        self.progress_bar.setValue(0)

        self.stage_value.setText("-")

        self.chunk_value.setText("0 / 0")

        self.elapsed_value.setText("00:00")

        self.remaining_value.setText("--:--")

        self.current_text.clear()

        self.log_view.clear()

        self.status_label.setText("Preparing...")

        self.cancel_button.setText("Cancel")

        self.start_time = None