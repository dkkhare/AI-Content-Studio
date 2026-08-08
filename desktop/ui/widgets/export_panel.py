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
                self.destination.text().strip(), self.preset.currentText()
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

    def refresh(self):
        running = self.controller.is_running()
        has_project = self.controller.project is not None
        has_preview = self.preview.rowCount() > 0
        self.export_button.setEnabled(has_project and has_preview and not running)
        self.cancel_button.setEnabled(running)
        for widget in (
            self.preset,
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
        self.progress.setValue(0)
        self.status.setText("Open a project to export.")
        self.refresh()

    def dispose(self):
        self.clear()
