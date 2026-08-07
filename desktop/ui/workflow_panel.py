from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class WorkflowPanel(QWidget):
    """Live monitor and controls for the Milestone 12 processing pipeline."""

    pauseRequested = Signal()
    resumeRequested = Signal()
    cancelRequested = Signal()
    resetRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_stage = ""
        self._running = False
        self._paused = False
        self._build_ui()
        self.reset()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        layout.addWidget(QLabel("<h2>AI Processing Pipeline</h2>"))

        self.status_label = QLabel("Ready")
        self.stage_label = QLabel("No active stage")
        self.message_label = QLabel("")
        self.message_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        layout.addWidget(self.stage_label)

        self.overall_progress = QProgressBar(self)
        self.overall_progress.setRange(0, 100)
        self.overall_progress.setFormat("Overall %p%")
        layout.addWidget(self.overall_progress)

        self.stage_progress = QProgressBar(self)
        self.stage_progress.setRange(0, 100)
        self.stage_progress.setFormat("Stage %p%")
        layout.addWidget(self.stage_progress)
        layout.addWidget(self.message_label)

        controls = QHBoxLayout()
        self.pause_button = QPushButton("Pause", self)
        self.resume_button = QPushButton("Resume", self)
        self.cancel_button = QPushButton("Cancel", self)
        self.reset_button = QPushButton("Reset", self)

        self.pause_button.clicked.connect(self.pauseRequested.emit)
        self.resume_button.clicked.connect(self.resumeRequested.emit)
        self.cancel_button.clicked.connect(self.cancelRequested.emit)
        self.reset_button.clicked.connect(self._request_reset)

        controls.addWidget(self.pause_button)
        controls.addWidget(self.resume_button)
        controls.addWidget(self.cancel_button)
        controls.addStretch(1)
        controls.addWidget(self.reset_button)
        layout.addLayout(controls)
        layout.addStretch(1)

    def bind_controller(self, controller) -> None:
        """Connect this panel to a PipelineController instance."""
        self.pauseRequested.connect(controller.pause)
        self.resumeRequested.connect(controller.resume)
        self.cancelRequested.connect(controller.cancel)

        controller.started.connect(self.processing_started)
        controller.progressChanged.connect(self.update_progress)
        controller.paused.connect(self.processing_paused)
        controller.resumed.connect(self.processing_resumed)
        controller.cancelled.connect(self.processing_cancelled)
        controller.completed.connect(self.processing_completed)
        controller.failed.connect(self.processing_failed)

    def processing_started(self) -> None:
        self._running = True
        self._paused = False
        self.status_label.setText("Running")
        self._update_controls()

    def update_progress(self, progress) -> None:
        self.current_stage = str(getattr(progress, "current_stage", "") or "")
        self.stage_label.setText(self.current_stage or "Processing")
        self.overall_progress.setValue(int(getattr(progress, "percent", 0)))
        self.stage_progress.setValue(int(getattr(progress, "stage_percent", 0)))
        self.message_label.setText(str(getattr(progress, "message", "") or ""))

        status = str(getattr(progress, "status", "") or "")
        if status:
            self.status_label.setText(status.replace("_", " ").title())

    def processing_paused(self) -> None:
        self._paused = True
        self.status_label.setText("Paused")
        self._update_controls()

    def processing_resumed(self) -> None:
        self._paused = False
        self.status_label.setText("Running")
        self._update_controls()

    def processing_cancelled(self) -> None:
        self._running = False
        self._paused = False
        self.status_label.setText("Cancelled")
        self._update_controls()

    def processing_completed(self, state=None) -> None:
        self._running = False
        self._paused = False
        self.status_label.setText("Completed")
        self.overall_progress.setValue(100)
        self.stage_progress.setValue(100)
        self._update_controls()

    def processing_failed(self, message: str) -> None:
        self._running = False
        self._paused = False
        self.status_label.setText("Failed")
        self.message_label.setText(str(message))
        self._update_controls()

    def _request_reset(self) -> None:
        if self._running:
            return
        self.reset()
        self.resetRequested.emit()

    def reset(self) -> None:
        self.current_stage = ""
        self._running = False
        self._paused = False
        self.status_label.setText("Ready")
        self.stage_label.setText("No active stage")
        self.message_label.clear()
        self.overall_progress.setValue(0)
        self.stage_progress.setValue(0)
        self._update_controls()

    def _update_controls(self) -> None:
        self.pause_button.setEnabled(self._running and not self._paused)
        self.resume_button.setEnabled(self._running and self._paused)
        self.cancel_button.setEnabled(self._running)
        self.reset_button.setEnabled(not self._running)

    def current(self) -> str:
        return self.current_stage
