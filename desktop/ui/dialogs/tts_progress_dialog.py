from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


class TTSProgressDialog(QDialog):
    """Modal progress view that also owns user-requested cancellation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generating Narration")
        self.resize(700, 520)
        self.setModal(True)
        self.start_time = None
        self.controller = None
        self._terminal = False
        self._build_ui()
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._update_elapsed)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        self.status_label = QLabel("Preparing...")
        layout.addWidget(self.status_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        group = QGroupBox("Generation Status")
        grid = QGridLayout(group)
        self.stage_value = QLabel("-")
        self.chunk_value = QLabel("0 / 0")
        self.elapsed_value = QLabel("00:00")
        self.remaining_value = QLabel("--:--")
        for row, (label, widget) in enumerate((
            ("Stage:", self.stage_value),
            ("Chunk:", self.chunk_value),
            ("Elapsed:", self.elapsed_value),
            ("Remaining:", self.remaining_value),
        )):
            grid.addWidget(QLabel(label), row, 0)
            grid.addWidget(widget, row, 1)
        layout.addWidget(group)

        current_group = QGroupBox("Current Text")
        current_layout = QVBoxLayout(current_group)
        self.current_text = QTextEdit()
        self.current_text.setReadOnly(True)
        current_layout.addWidget(self.current_text)
        layout.addWidget(current_group)

        log_group = QGroupBox("Generation Log")
        log_layout = QVBoxLayout(log_group)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        log_layout.addWidget(self.log_view)
        layout.addWidget(log_group)

        buttons = QHBoxLayout()
        buttons.addStretch()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self._button_clicked)
        buttons.addWidget(self.cancel_button)
        layout.addLayout(buttons)

    def set_controller(self, controller):
        if self.controller is controller:
            return
        if self.controller is not None:
            raise RuntimeError("Progress dialog is already bound to a controller.")
        self.controller = controller
        controller.generation_started.connect(self.on_started)
        controller.generation_progress.connect(self.on_progress)
        controller.generation_finished.connect(self.on_finished)
        controller.generation_failed.connect(self.on_failed)
        controller.generation_cancelled.connect(self.on_cancelled)
        controller.log_message.connect(self.append_log)

    def _button_clicked(self):
        if self._terminal:
            self.accept()
        elif self.controller is not None:
            self.cancel_button.setEnabled(False)
            self.status_label.setText("Cancelling narration...")
            self.controller.cancel()

    def start_timer(self):
        self.start_time = datetime.now()
        self.timer.start()

    def stop_timer(self):
        self.timer.stop()

    def _update_elapsed(self):
        if self.start_time is None:
            return
        seconds = int((datetime.now() - self.start_time).total_seconds())
        self.elapsed_value.setText(f"{seconds // 60:02}:{seconds % 60:02}")

    def append_log(self, message):
        self.log_view.append(str(message))

    def on_started(self):
        self._terminal = False
        self.cancel_button.setText("Cancel")
        self.cancel_button.setEnabled(True)
        self.status_label.setText("Generating narration...")
        self.progress_bar.setValue(0)
        self.start_timer()

    def on_progress(self, progress):
        percent = max(0, min(100, int(getattr(progress, "percent", 0))))
        current = int(getattr(progress, "current_chunk", 0))
        total = int(getattr(progress, "total_chunks", 0))
        remaining = max(0, int(getattr(progress, "remaining_seconds", 0) or 0))
        self.progress_bar.setValue(percent)
        self.stage_value.setText(str(getattr(progress, "stage", "") or "-"))
        self.chunk_value.setText(f"{current} / {total}")
        self.current_text.setPlainText(str(getattr(progress, "current_text", "")))
        self.remaining_value.setText(
            f"{remaining // 60:02}:{remaining % 60:02}" if remaining else "--:--"
        )

    def _set_terminal(self, status, message, *, success=False):
        self.stop_timer()
        self._terminal = True
        self.status_label.setText(status)
        self.append_log(message)
        if success:
            self.progress_bar.setValue(100)
        self.cancel_button.setText("Close")
        self.cancel_button.setEnabled(True)

    def on_finished(self, session):
        self._set_terminal(
            "Narration generated successfully.", "Generation completed.", success=True
        )

    def on_failed(self, message):
        self._set_terminal("Generation failed.", str(message))

    def on_cancelled(self):
        self._set_terminal("Generation cancelled.", "Operation cancelled.")

    def reset(self):
        self.stop_timer()
        self._terminal = False
        self.progress_bar.setValue(0)
        self.stage_value.setText("-")
        self.chunk_value.setText("0 / 0")
        self.elapsed_value.setText("00:00")
        self.remaining_value.setText("--:--")
        self.current_text.clear()
        self.log_view.clear()
        self.status_label.setText("Preparing...")
        self.cancel_button.setText("Cancel")
        self.cancel_button.setEnabled(True)
        self.start_time = None

    def closeEvent(self, event):
        if (
            not self._terminal
            and self.controller is not None
            and self.controller.is_running()
        ):
            self.controller.cancel()
        self.stop_timer()
        event.accept()
