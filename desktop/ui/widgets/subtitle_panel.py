from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,\n    QSlider,\n    QTableWidget,
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
        self._audio_player = None
        self._audio_path = ""
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

        preview = QHBoxLayout()
        self.play_button = QPushButton("Play Narration")
        self.stop_button = QPushButton("Stop")
        self.timeline = QSlider(Qt.Horizontal)
        self.timeline.setRange(0, 0)
        self.preview_text = QLabel("No active cue")
        preview.addWidget(self.play_button)
        preview.addWidget(self.stop_button)
        preview.addWidget(self.timeline, 1)
        preview.addWidget(self.preview_text)
        layout.addLayout(preview)

        self.status = QLabel("Open a project to create subtitles.")
        layout.addWidget(self.status)

    def _connect(self):
        self.generate_button.clicked.connect(self.generate_subtitles)
        self.import_button.clicked.connect(self.import_subtitles)
        self.apply_button.clicked.connect(self.apply_edits)
        self.export_button.clicked.connect(self.export_subtitles)
        self.play_button.clicked.connect(self.play_audio)
        self.stop_button.clicked.connect(self.stop_audio)
        self.timeline.valueChanged.connect(self.sync_position)

    def set_project(self, project):
        try:
            document = self.controller.set_project(project)
            context = self.controller.project_context()
            self._audio_path = context["audio_path"]
            if context["text"]:
                self.source_text.setPlainText(context["text"])
            if context["duration_seconds"] > 0:
                self.duration.setValue(context["duration_seconds"])
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
            index.setFlags(index.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, index)
            self.table.setItem(row, 1, QTableWidgetItem(format_timestamp(cue.start_ms)))
            self.table.setItem(row, 2, QTableWidgetItem(format_timestamp(cue.end_ms)))
            self.table.setItem(row, 3, QTableWidgetItem(cue.text))
        maximum = document.cues[-1].end_ms if document.cues else 0
        self.timeline.setRange(0, maximum)
        self.refresh()

    def play_audio(self):
        if not self._audio_path:
            self.status.setText("No project narration audio is available.")
            return
        try:
            if self._audio_player is None:
                from backend.audio.player import AudioPlayer
                self._audio_player = AudioPlayer(self)
                self._audio_player.positionChanged.connect(self._position_changed)
                self._audio_player.durationChanged.connect(self._duration_changed)
            self._audio_player.play(self._audio_path)
            self.status.setText("Playing narration.")
        except Exception as exc:
            self._show_error("Unable to play narration", exc)

    def stop_audio(self):
        if self._audio_player is not None:
            self._audio_player.stop()

    def _position_changed(self, progress):
        position = int(getattr(progress, "position", 0))
        self.timeline.blockSignals(True)
        self.timeline.setValue(position)
        self.timeline.blockSignals(False)
        self.sync_position(position)

    def _duration_changed(self, duration):
        if int(duration) > 0:
            self.timeline.setMaximum(int(duration))
            self.duration.setValue(int(duration) / 1000.0)

    def sync_position(self, position_ms):
        cue = self.controller.cue_at(position_ms)
        if cue is None:
            self.table.clearSelection()
            self.preview_text.setText("No active cue")
        else:
            self.table.selectRow(cue.index - 1)
            self.preview_text.setText(cue.text)
        if self._audio_player is not None and self.sender() is self.timeline:
            self._audio_player.seek(int(position_ms))

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
        self.stop_audio()
        self._audio_path = ""
        self.source_text.clear()
        self.controller.set_project(None)
        self._show_document(self.controller.document)
        self.status.setText("Open a project to create subtitles.")
        self.refresh()

    def dispose(self):
        self.clear()
        if self._audio_player is not None:
            self._audio_player.close()
            self._audio_player = None
