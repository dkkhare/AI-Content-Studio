from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from backend.subtitles import format_timestamp
from desktop.controllers.subtitle_controller import SubtitleDesktopController


class SubtitlePanel(QWidget):
    """Generate, import, edit, preview and export project subtitles."""

    subtitlesChanged = Signal(object)

    def __init__(self, parent=None, *, controller=None):
        super().__init__(parent)
        self.controller = controller or SubtitleDesktopController()
        self._build_ui()
        self._connect()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Subtitle Workbench"))

        form = QFormLayout()
        self.source_text = QTextEdit()
        self.source_text.setPlaceholderText("Paste narration text...")
        self.source_text.setMinimumHeight(120)
        form.addRow("Narration text", self.source_text)

        self.duration = QDoubleSpinBox()
        self.duration.setRange(0.1, 24 * 60 * 60)
        self.duration.setDecimals(3)
        self.duration.setValue(60)
        self.duration.setSuffix(" seconds")
        form.addRow("Audio duration", self.duration)

        self.format = QComboBox()
        self.format.addItems(["srt", "vtt"])
        form.addRow("Project format", self.format)
        layout.addLayout(form)

        actions = QHBoxLayout()
        self.generate_button = QPushButton("Generate")
        self.import_button = QPushButton("Import...")
        self.apply_button = QPushButton("Apply Cue Edits")
        self.export_button = QPushButton("Export...")
        for button in (
            self.generate_button,
            self.import_button,
            self.apply_button,
            self.export_button,
        ):
            actions.addWidget(button)
        actions.addStretch()
        layout.addLayout(actions)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["#", "Start", "End", "Text"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.status = QLabel("Open a project to create subtitles.")
        layout.addWidget(self.status)

    def _connect(self):
        self.generate_button.clicked.connect(self.generate_subtitles)
        self.import_button.clicked.connect(self.import_subtitles)
        self.apply_button.clicked.connect(self.apply_edits)
        self.export_button.clicked.connect(self.export_subtitles)

    def set_project(self, project):
        try:
            document = self.controller.set_project(project)
            self._show_document(document)
            self.status.setText(
                "Project subtitles loaded." if document.cues else "No project subtitles yet."
            )
        except Exception as exc:
            self._show_error("Unable to load project subtitles", exc)
        self.refresh()

    def generate_subtitles(self):
        try:
            document = self.controller.generate(
                self.source_text.toPlainText(),
                self.duration.value(),
                format=self.format.currentText(),
            )
            self._show_document(document)
            self.status.setText(f"Generated {len(document.cues)} cues.")
            self.subtitlesChanged.emit(document)
        except Exception as exc:
            self._show_error("Unable to generate subtitles", exc)

    def import_subtitles(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Subtitles", "", "Subtitle Files (*.srt *.vtt)"
        )
        if not path:
            return
        try:
            document = self.controller.import_file(path)
            self._show_document(document)
            self.status.setText(f"Imported {len(document.cues)} cues.")
            self.subtitlesChanged.emit(document)
        except Exception as exc:
            self._show_error("Unable to import subtitles", exc)

    def export_subtitles(self):
        selected = self.format.currentText()
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Subtitles",
            f"subtitles.{selected}",
            "SRT (*.srt);;WebVTT (*.vtt)",
        )
        if not path:
            return
        try:
            target = self.controller.export_file(path)
            self.status.setText(f"Exported {target.name}.")
        except Exception as exc:
            self._show_error("Unable to export subtitles", exc)

    def apply_edits(self):
        rows = []
        try:
            for row in range(self.table.rowCount()):
                rows.append({
                    "start": self.table.item(row, 1).text(),
                    "end": self.table.item(row, 2).text(),
                    "text": self.table.item(row, 3).text(),
                })
            document = self.controller.replace_cues(rows)
            self._show_document(document)
            self.status.setText(f"Applied edits to {len(document.cues)} cues.")
            self.subtitlesChanged.emit(document)
        except Exception as exc:
            self._show_error("Invalid cue edits", exc)

    def _show_document(self, document):
        self.table.setRowCount(len(document.cues))
        for row, cue in enumerate(document.cues):
            index = QTableWidgetItem(str(cue.index))
            index.setFlags(index.flags() & ~index.flags().ItemIsEditable)
            self.table.setItem(row, 0, index)
            self.table.setItem(row, 1, QTableWidgetItem(format_timestamp(cue.start_ms)))
            self.table.setItem(row, 2, QTableWidgetItem(format_timestamp(cue.end_ms)))
            self.table.setItem(row, 3, QTableWidgetItem(cue.text))

    def _show_error(self, title, error):
        self.status.setText(str(error))
        QMessageBox.warning(self, title, str(error))

    def refresh(self):
        has_project = self.controller.project is not None
        has_cues = bool(self.controller.document.cues)
        self.generate_button.setEnabled(has_project)
        self.import_button.setEnabled(has_project)
        self.apply_button.setEnabled(has_cues)
        self.export_button.setEnabled(has_cues)

    def clear(self):
        self.source_text.clear()
        self.controller.set_project(None)
        self._show_document(self.controller.document)
        self.status.setText("Open a project to create subtitles.")
        self.refresh()

    def dispose(self):
        self.clear()
