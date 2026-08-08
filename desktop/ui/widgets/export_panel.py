from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from desktop.controllers.export_controller import ExportDesktopController


class ExportPanel(QWidget):
    """Preview and publish verified project export packages."""

    packageExported = Signal(str)

    def __init__(self, parent=None, *, controller=None):
        super().__init__(parent)
        self.controller = controller or ExportDesktopController(self)
        self._build_ui()
        self._connect()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Export & Publishing"))

        form = QFormLayout()
        self.preset = QComboBox()
        form.addRow("Preset", self.preset)

        self.batch_mode = QComboBox()
        self.batch_mode.addItem("Export only", "export")
        self.batch_mode.addItem("Render then export", "render_export")
        form.addRow("Batch mode", self.batch_mode)

        destination_row = QHBoxLayout()
        self.destination = QLineEdit()
        self.destination_button = QPushButton("Choose Parent...")
        destination_row.addWidget(self.destination, 1)
        destination_row.addWidget(self.destination_button)
        form.addRow("Package destination", destination_row)
        layout.addLayout(form)

        self.preview = QTableWidget(0, 4)
        self.preview.setHorizontalHeaderLabels(["Role", "File", "Size", "Required"])
        self.preview.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.preview)

        actions = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh Preview")
        self.export_button = QPushButton("Export Package")
        self.cancel_button = QPushButton("Cancel")
        actions.addWidget(self.refresh_button)
        actions.addStretch()
        actions.addWidget(self.export_button)
        actions.addWidget(self.cancel_button)
        layout.addLayout(actions)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.status = QLabel("Open a project to export.")
        layout.addWidget(self.progress)
        layout.addWidget(self.status)

        layout.addWidget(QLabel("Persistent Batch Queue"))
        self.queue_table = QTableWidget(0, 7)
        self.queue_table.setHorizontalHeaderLabels(
            [
                "Status",
                "Phase",
                "Mode",
                "Preset",
                "Destination",
                "Attempts",
                "Error",
            ]
        )
        self.queue_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.queue_table)

        batch_actions = QHBoxLayout()
        self.enqueue_button = QPushButton("Add Current to Queue")
        self.run_batch_button = QPushButton("Run Pending")
        self.retry_button = QPushButton("Retry Selected")
        self.cancel_batch_button = QPushButton("Cancel Batch")
        batch_actions.addWidget(self.enqueue_button)
        batch_actions.addWidget(self.run_batch_button)
        batch_actions.addWidget(self.retry_button)
        batch_actions.addStretch()
        batch_actions.addWidget(self.cancel_batch_button)
        layout.addLayout(batch_actions)

    def _connect(self):
        self.preset.currentTextChanged.connect(self._preset_changed)
        self.destination_button.clicked.connect(self.choose_destination_parent)
        self.refresh_button.clicked.connect(self.refresh_preview)
        self.export_button.clicked.connect(self.export_package)
        self.cancel_button.clicked.connect(self.controller.cancel)
        self.controller.exportStarted.connect(self._started)
        self.controller.exportProgress.connect(self._progress)
        self.controller.exportFinished.connect(self._finished)
        self.controller.exportFailed.connect(self._failed)
        self.controller.exportCancelled.connect(self._cancelled)
        self.enqueue_button.clicked.connect(self.enqueue_current)
        self.run_batch_button.clicked.connect(self.run_batch)
        self.retry_button.clicked.connect(self.retry_selected)
        self.cancel_batch_button.clicked.connect(self.controller.cancel)
        self.queue_table.itemSelectionChanged.connect(self.refresh)
        self.controller.batchStarted.connect(self._batch_started)
        self.controller.batchJobChanged.connect(self._batch_job_changed)
        self.controller.batchFinished.connect(self._batch_finished)
        self.controller.batchFailed.connect(self._batch_failed)

    def set_project(self, project):
        try:
            context = self.controller.set_project(project)
            self.preset.blockSignals(True)
            self.preset.clear()
            self.preset.addItems(context["presets"])
            index = self.preset.findText("publishing")
            self.preset.setCurrentIndex(index if index >= 0 else 0)
            self.preset.blockSignals(False)
            self.destination.setText(
                self.controller.default_destination(self.preset.currentText())
            )
            self.refresh_preview()
            self.refresh_queue()
        except Exception as exc:
            self._failed(str(exc))
        self.refresh()

    def _preset_changed(self, preset):
        if self.controller.project is not None and preset:
            self.destination.setText(self.controller.default_destination(preset))
            self.refresh_preview()

    def choose_destination_parent(self):
        parent = QFileDialog.getExistingDirectory(
            self, "Select Export Parent Directory", ""
        )
        if parent:
            self.destination.setText(
                self.controller.default_destination(
                    self.preset.currentText(), parent=parent
                )
            )

    def refresh_preview(self):
        self.preview.setRowCount(0)
        if self.controller.project is None or not self.preset.currentText():
            self.refresh()
            return
        try:
            rows = self.controller.preview(self.preset.currentText())
            self.preview.setRowCount(len(rows))
            for row, asset in enumerate(rows):
                values = (
                    asset["role"],
                    Path(asset["path"]).name,
                    self._format_size(asset["size"]),
                    "Yes" if asset["required"] else "No",
                )
                for column, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.preview.setItem(row, column, item)
            self.status.setText(f"{len(rows)} assets ready for export.")
        except Exception as exc:
            self.status.setText(str(exc))
        self.refresh()

    @staticmethod
    def _format_size(value):
        size = float(value)
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024 or unit == "GB":
                return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
            size /= 1024

    def validation_error(self):
        if self.controller.project is None:
            return "Open a project before exporting."
        if not self.destination.text().strip():
            return "Choose an export package destination."
        if Path(self.destination.text()).exists():
            return "Export destination already exists; choose a new package name."
        try:
            self.controller.preview(self.preset.currentText())
        except Exception as exc:
            return str(exc)
        return ""

    def export_package(self):
        error = self.validation_error()
        if error:
            QMessageBox.warning(self, "Export", error)
            self.status.setText(error)
            return
        try:
            self.controller.start_export(
                self.destination.text().strip(),
                self.preset.currentText(),
                mode=self.batch_mode.currentData(),
            )
        except Exception as exc:
            self._failed(str(exc))

    def _started(self):
        self.progress.setValue(0)
        self.status.setText("Exporting package...")
        self.refresh()

    def _progress(self, value):
        self.progress.setValue(round(value))

    def _finished(self, manifest, output):
        self.progress.setValue(100)
        self.status.setText(
            f"Exported {len(manifest.assets)} assets to {Path(output).name}."
        )
        self.packageExported.emit(output)
        self.refresh()

    def _failed(self, message):
        self.status.setText(str(message))
        self.refresh()

    def _cancelled(self):
        self.status.setText("Project export cancelled.")
        self.refresh()


    def refresh_queue(self):
        rows = self.controller.queue_rows()
        self.queue_table.setRowCount(len(rows))
        for row, job in enumerate(rows):
            values = (
                job["status"],
                job["phase"],
                job["mode"],
                job["preset"],
                Path(job["destination"]).name,
                job["attempts"],
                job["error"],
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if column == 0:
                    item.setData(Qt.UserRole, job["id"])
                self.queue_table.setItem(row, column, item)
        self.refresh()

    def enqueue_current(self):
        error = self.validation_error()
        if error:
            QMessageBox.warning(self, "Batch Export", error)
            self.status.setText(error)
            return
        try:
            job = self.controller.enqueue_current(
                self.destination.text().strip(), self.preset.currentText()
            )
            self.status.setText(f"Queued {Path(job.destination).name}.")
            self.refresh_queue()
        except Exception as exc:
            self._failed(str(exc))

    def run_batch(self):
        try:
            self.controller.start_batch()
        except Exception as exc:
            self._failed(str(exc))

    def selected_job_id(self):
        row = self.queue_table.currentRow()
        if row < 0 or self.queue_table.item(row, 0) is None:
            return ""
        return str(self.queue_table.item(row, 0).data(Qt.UserRole) or "")

    def retry_selected(self):
        job_id = self.selected_job_id()
        if not job_id:
            self.status.setText("Select a failed or cancelled batch job.")
            return
        try:
            self.controller.retry_job(job_id)
            self.status.setText("Selected job queued for retry.")
            self.refresh_queue()
        except Exception as exc:
            self._failed(str(exc))

    def _batch_started(self):
        self.status.setText("Running batch export queue...")
        self.refresh()

    def _batch_job_changed(self, job):
        self.status.setText(
            f"{Path(job.destination).name}: {job.status}"
            + (f" — {job.error}" if job.error else "")
        )
        self.refresh_queue()

    def _batch_finished(self, jobs):
        counts = self.controller.queue.counts()
        self.status.setText(
            f"Batch finished: {counts['completed']} completed, "
            f"{counts['failed']} failed, {counts['cancelled']} cancelled."
        )
        self.refresh_queue()

    def _batch_failed(self, message):
        self.status.setText(f"Batch runner failed: {message}")
        self.refresh_queue()

    def refresh(self):
        running = self.controller.is_running()
        has_project = self.controller.project is not None
        has_preview = self.preview.rowCount() > 0
        rows = self.controller.queue_rows()
        has_pending = any(job["status"] == "pending" for job in rows)
        selected = self.selected_job_id()
        retryable = bool(
            selected
            and self.controller.queue
            and self.controller.queue.get(selected).status in {"failed", "cancelled"}
        )
        self.export_button.setEnabled(has_project and has_preview and not running)
        self.cancel_button.setEnabled(running)
        self.enqueue_button.setEnabled(has_project and has_preview and not running)
        self.run_batch_button.setEnabled(has_pending and not running)
        self.retry_button.setEnabled(retryable and not running)
        self.cancel_batch_button.setEnabled(running)
        for widget in (
            self.preset,
            self.batch_mode,
            self.destination,
            self.destination_button,
            self.refresh_button,
        ):
            widget.setEnabled(not running)

    def clear(self):
        self.controller.cleanup()
        self.controller.set_project(None)
        self.preset.clear()
        self.destination.clear()
        self.preview.setRowCount(0)
        self.queue_table.setRowCount(0)
        self.progress.setValue(0)
        self.status.setText("Open a project to export.")
        self.refresh()

    def dispose(self):
        self.clear()
