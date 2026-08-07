from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


class WorkflowPanel(QWidget):
    """Live monitor and persistent queue controls for Milestone 12."""

    startRequested = Signal()
    pauseRequested = Signal()
    resumeRequested = Signal()
    cancelRequested = Signal()
    resetRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_stage = ""
        self._running = False
        self._paused = False
        self._has_project = False
        self._controller = None
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
        self.start_button = QPushButton("Queue Processing", self)
        self.pause_button = QPushButton("Pause Current", self)
        self.resume_button = QPushButton("Resume Current", self)
        self.cancel_button = QPushButton("Cancel Current", self)
        self.reset_button = QPushButton("Reset Monitor", self)

        self.start_button.clicked.connect(self.startRequested.emit)
        self.pause_button.clicked.connect(self._pause_current)
        self.resume_button.clicked.connect(self._resume_current)
        self.cancel_button.clicked.connect(self._cancel_current)
        self.reset_button.clicked.connect(self._request_reset)

        controls.addWidget(self.start_button)
        controls.addWidget(self.pause_button)
        controls.addWidget(self.resume_button)
        controls.addWidget(self.cancel_button)
        controls.addStretch(1)
        controls.addWidget(self.reset_button)
        layout.addLayout(controls)

        layout.addWidget(QLabel("<b>Processing Queue</b>"))
        self.queue_tree = QTreeWidget(self)
        self.queue_tree.setColumnCount(5)
        self.queue_tree.setHeaderLabels(
            ["Project", "Status", "Progress", "Priority", "Job ID"]
        )
        self.queue_tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.queue_tree.setRootIsDecorated(False)
        header = self.queue_tree.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.queue_tree.itemSelectionChanged.connect(self._update_queue_actions)
        layout.addWidget(self.queue_tree, 1)

        queue_controls = QHBoxLayout()
        self.cancel_selected_button = QPushButton("Cancel Selected", self)
        self.retry_selected_button = QPushButton("Retry Selected", self)
        self.refresh_queue_button = QPushButton("Refresh Queue", self)
        self.cancel_selected_button.clicked.connect(self._cancel_selected)
        self.retry_selected_button.clicked.connect(self._retry_selected)
        self.refresh_queue_button.clicked.connect(self._refresh_queue)
        queue_controls.addWidget(self.cancel_selected_button)
        queue_controls.addWidget(self.retry_selected_button)
        queue_controls.addWidget(self.refresh_queue_button)
        queue_controls.addStretch(1)
        layout.addLayout(queue_controls)

    def bind_controller(self, controller) -> None:
        self._controller = controller

        controller.started.connect(self.processing_started)
        controller.progressChanged.connect(self.update_progress)
        controller.paused.connect(self.processing_paused)
        controller.resumed.connect(self.processing_resumed)
        controller.cancelled.connect(self.processing_cancelled)
        controller.completed.connect(self.processing_completed)
        controller.failed.connect(self.processing_failed)

        controller.queueChanged.connect(self.update_queue)
        controller.jobUpdated.connect(self._queue_job_updated)
        controller.jobFinished.connect(self._queue_job_finished)
        controller.queueRecoveryError.connect(self._queue_recovery_error)

        self.update_queue(controller.queue_records())

    def set_project_available(self, available: bool) -> None:
        self._has_project = bool(available)
        self._update_controls()

    # --------------------------------------------------
    # Direct/current processing monitor
    # --------------------------------------------------

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

    # --------------------------------------------------
    # Queue UI
    # --------------------------------------------------

    def update_queue(self, records) -> None:
        selected_id = self._selected_job_id()
        self.queue_tree.clear()

        active_record = None
        for record in records or []:
            job_id = str(record.get("job_id", ""))
            root = str(record.get("project_root", ""))
            project_name = Path(root).name if root else "Unknown Project"
            status = str(record.get("status", "queued"))
            priority = int(record.get("priority", 0))
            progress_value = max(0, min(100, int(record.get("progress", 0))))

            item = QTreeWidgetItem(
                [project_name, status.title(), "", str(priority), job_id[:12]]
            )
            item.setData(0, Qt.UserRole, job_id)
            item.setToolTip(0, root)
            if record.get("error"):
                item.setToolTip(1, str(record.get("error")))
            self.queue_tree.addTopLevelItem(item)

            bar = QProgressBar(self.queue_tree)
            bar.setRange(0, 100)
            bar.setValue(progress_value)
            bar.setTextVisible(True)
            bar.setFormat("%p%")
            self.queue_tree.setItemWidget(item, 2, bar)

            if selected_id and selected_id == job_id:
                self.queue_tree.setCurrentItem(item)

            if status in {"running", "paused"} and active_record is None:
                active_record = record

        if active_record is not None:
            status = str(active_record.get("status", "running"))
            self._running = True
            self._paused = status == "paused"
            self.status_label.setText(status.title())
            self.stage_label.setText(
                f"Queued project: {Path(str(active_record.get('project_root', ''))).name}"
            )
            self.overall_progress.setValue(int(active_record.get("progress", 0)))
        elif not (
            self._controller is not None and getattr(self._controller, "running", False)
        ):
            self._running = False
            self._paused = False

        self._update_queue_actions()
        self._update_controls()

    def _queue_job_updated(self, record) -> None:
        self.update_queue(self._controller.queue_records() if self._controller else [])

    def _queue_job_finished(self, record) -> None:
        status = str(record.get("status", "completed"))
        self.status_label.setText(status.title())
        if status == "completed":
            self.overall_progress.setValue(100)
        if record.get("error"):
            self.message_label.setText(str(record.get("error")))
        self.update_queue(self._controller.queue_records() if self._controller else [])

    def _queue_recovery_error(self, message: str) -> None:
        self.message_label.setText(str(message))

    def _selected_job_id(self) -> str:
        item = self.queue_tree.currentItem()
        if item is None:
            return ""
        return str(item.data(0, Qt.UserRole) or "")

    def _selected_status(self) -> str:
        item = self.queue_tree.currentItem()
        if item is None:
            return ""
        return item.text(1).strip().lower()

    def _cancel_selected(self) -> None:
        if self._controller is None:
            return
        job_id = self._selected_job_id()
        if job_id:
            self._controller.cancel_job(job_id)

    def _retry_selected(self) -> None:
        if self._controller is None:
            return
        job_id = self._selected_job_id()
        if not job_id:
            return
        try:
            self._controller.retry_job(job_id)
        except Exception as exc:
            self.message_label.setText(f"Retry failed: {exc}")

    def _refresh_queue(self) -> None:
        if self._controller is not None:
            self.update_queue(self._controller.queue_records())

    def _update_queue_actions(self) -> None:
        status = self._selected_status()
        self.cancel_selected_button.setEnabled(status in {"queued", "running", "paused"})
        self.retry_selected_button.setEnabled(status in {"failed", "cancelled"})

    # --------------------------------------------------
    # Current job controls
    # --------------------------------------------------

    def _pause_current(self) -> None:
        if self._controller is None:
            return
        if self._controller.queue_running:
            self._controller.pause_queue()
        else:
            self._controller.pause()

    def _resume_current(self) -> None:
        if self._controller is None:
            return
        if self._controller.queue_running:
            self._controller.resume_queue()
        else:
            self._controller.resume()

    def _cancel_current(self) -> None:
        if self._controller is None:
            return
        current = self._controller.job_queue.current
        if current is not None:
            self._controller.cancel_job(current.job_id)
        else:
            self._controller.cancel()

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
        self._update_queue_actions()

    def _update_controls(self) -> None:
        self.start_button.setEnabled(self._has_project)
        self.pause_button.setEnabled(self._running and not self._paused)
        self.resume_button.setEnabled(self._running and self._paused)
        self.cancel_button.setEnabled(self._running)
        self.reset_button.setEnabled(not self._running)

    def current(self) -> str:
        return self.current_stage
