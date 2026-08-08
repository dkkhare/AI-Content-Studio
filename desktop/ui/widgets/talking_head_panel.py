from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from desktop.controllers.talking_head_controller import TalkingHeadController


class TalkingHeadPanel(QWidget):
    def __init__(self, parent=None, *, controller=None):
        super().__init__(parent)
        self.controller = controller or TalkingHeadController(self)
        self._build()
        self._connect()
        self.refresh()

    def _path_row(self, form, label, directory=False):
        edit = QLineEdit()
        button = QPushButton("Browse...")
        row = QHBoxLayout()
        row.addWidget(edit, 1)
        row.addWidget(button)
        form.addRow(label, row)
        if directory:
            button.clicked.connect(
                lambda: self._browse_directory(edit, f"Select {label}")
            )
        return edit, button

    def _build(self):
        root = QVBoxLayout(self)
        root.addWidget(QLabel("Talking Head Book Series"))
        form = QFormLayout()
        self.book, self.book_button = self._path_row(form, "Complete book")
        self.portrait, self.portrait_button = self._path_row(form, "Writer portrait")
        self.voice, self.voice_button = self._path_row(form, "Writer voice sample")
        self.sadtalker, self.sadtalker_button = self._path_row(
            form, "SadTalker directory", True
        )
        self.python = QLineEdit(sys.executable)
        form.addRow("SadTalker Python", self.python)
        self.transcript = QTextEdit()
        self.transcript.setPlaceholderText("Exact words spoken in the voice sample")
        self.transcript.setMaximumHeight(90)
        form.addRow("Voice transcript", self.transcript)
        self.episode_minutes = QDoubleSpinBox()
        self.episode_minutes.setRange(5, 60)
        self.episode_minutes.setValue(15)
        self.episode_minutes.setSuffix(" minutes")
        form.addRow("Episode target", self.episode_minutes)
        self.segment_seconds = QSpinBox()
        self.segment_seconds.setRange(15, 90)
        self.segment_seconds.setValue(45)
        self.segment_seconds.setSuffix(" seconds")
        form.addRow("GPU render segment", self.segment_seconds)
        self.words_per_minute = QSpinBox()
        self.words_per_minute.setRange(60, 300)
        self.words_per_minute.setValue(140)
        form.addRow("Narration speed", self.words_per_minute)
        self.output_directory, _ = self._path_row(form, "Series output", True)
        self.work_directory = QLineEdit()
        form.addRow("Recovery workspace", self.work_directory)
        root.addLayout(form)

        self.rights = QCheckBox(
            "I confirm permission to use this book, writer image, and writer voice."
        )
        root.addWidget(self.rights)
        actions = QHBoxLayout()
        self.preview_button = QPushButton("Preview Episodes")
        self.generate_button = QPushButton("Generate / Resume Series")
        self.cancel_button = QPushButton("Cancel")
        actions.addWidget(self.preview_button)
        actions.addStretch()
        actions.addWidget(self.generate_button)
        actions.addWidget(self.cancel_button)
        root.addLayout(actions)
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(150)
        self.preview_text.setPlaceholderText(
            "Preview displays ordered episode titles and estimated durations."
        )
        root.addWidget(self.preview_text)
        self.progress = QProgressBar()
        self.status = QLabel("Open a project and select the required inputs.")
        root.addWidget(self.progress)
        root.addWidget(self.status)

    def _connect(self):
        self.book_button.clicked.connect(
            lambda: self._browse_file(
                self.book, "Select Complete Book",
                "Books (*.pdf *.docx *.txt *.md)"
            )
        )
        self.portrait_button.clicked.connect(
            lambda: self._browse_file(
                self.portrait, "Select Writer Portrait",
                "Images (*.png *.jpg *.jpeg *.webp)"
            )
        )
        self.voice_button.clicked.connect(
            lambda: self._browse_file(
                self.voice, "Select Writer Voice",
                "Audio (*.wav *.mp3 *.flac *.ogg)"
            )
        )
        self.preview_button.clicked.connect(self.preview)
        self.generate_button.clicked.connect(self.generate)
        self.cancel_button.clicked.connect(self.controller.cancel)
        self.controller.generationStarted.connect(self._started)
        self.controller.generationProgress.connect(self._progress)
        self.controller.generationFinished.connect(self._finished)
        self.controller.generationFailed.connect(self._failed)
        self.controller.generationCancelled.connect(self._cancelled)

    def _browse_file(self, edit, title, filters):
        value, _ = QFileDialog.getOpenFileName(self, title, "", filters)
        if value:
            edit.setText(value)

    def _browse_directory(self, edit, title):
        value = QFileDialog.getExistingDirectory(self, title, edit.text())
        if value:
            edit.setText(value)

    def set_project(self, project):
        context = self.controller.set_project(project)
        self.output_directory.setText(context["output_directory"])
        self.work_directory.setText(context["work_directory"])
        self.refresh()

    def validation_error(self):
        if self.controller.project is None:
            return "Open a project first."
        files = (
            ("book", self.book.text()),
            ("writer portrait", self.portrait.text()),
            ("writer voice sample", self.voice.text()),
        )
        for label, value in files:
            if not Path(value).is_file():
                return f"Select a valid {label} file."
        if not (Path(self.sadtalker.text()) / "inference.py").is_file():
            return "Select a SadTalker directory containing inference.py."
        if not self.python.text().strip():
            return "Select the Python executable used by SadTalker."
        if not self.transcript.toPlainText().strip():
            return "Enter the exact voice-sample transcript."
        if not self.rights.isChecked():
            return "Confirm permission for the book, image, and voice."
        return ""

    def preview(self):
        if not Path(self.book.text()).is_file():
            QMessageBox.warning(self, "Talking Head Series", "Select a valid book.")
            return
        try:
            imported, plan = self.controller.preview(
                self.book.text(),
                episode_minutes=self.episode_minutes.value(),
                words_per_minute=self.words_per_minute.value(),
            )
            lines = [
                f"{item.number:03d}. {item.title} "
                f"(about {item.estimated_seconds / 60:.1f} minutes)"
                for item in plan.episodes
            ]
            self.preview_text.setPlainText(
                f"{len(imported.blocks)} source sections; "
                f"{len(plan.episodes)} planned episodes.\n" + "\n".join(lines)
            )
            self.status.setText("Preview complete; no source content was summarized.")
        except Exception as exc:
            self._failed(str(exc))

    def settings(self):
        return {
            "book": self.book.text().strip(),
            "portrait": self.portrait.text().strip(),
            "reference_audio": self.voice.text().strip(),
            "reference_text": self.transcript.toPlainText().strip(),
            "sadtalker_directory": self.sadtalker.text().strip(),
            "sadtalker_python": self.python.text().strip(),
            "episode_minutes": self.episode_minutes.value(),
            "segment_seconds": self.segment_seconds.value(),
            "words_per_minute": self.words_per_minute.value(),
            "output_directory": self.output_directory.text().strip(),
            "work_directory": self.work_directory.text().strip(),
            "rights_confirmed": self.rights.isChecked(),
            "size": 256,
            "preprocess": "crop",
            "enhancer": "",
        }

    def generate(self):
        error = self.validation_error()
        if error:
            QMessageBox.warning(self, "Talking Head Series", error)
            self.status.setText(error)
            return
        try:
            self.controller.start(**self.settings())
        except Exception as exc:
            self._failed(str(exc))

    def _started(self):
        self.progress.setValue(0)
        self.status.setText("Generating talking-head episode series...")
        self.refresh()

    def _progress(self, value, message):
        self.progress.setValue(round(value))
        self.status.setText(message)

    def _finished(self, result):
        self.progress.setValue(100)
        self.status.setText(
            f"Completed {len(result.episodes)} episodes in {result.output_directory}."
        )
        self.refresh()

    def _failed(self, message):
        self.status.setText(str(message))
        self.refresh()

    def _cancelled(self):
        self.status.setText("Cancelled safely. Use Generate / Resume to continue.")
        self.refresh()

    def refresh(self):
        running = self.controller.is_running()
        self.preview_button.setEnabled(not running)
        self.generate_button.setEnabled(
            self.controller.project is not None and not running
        )
        self.cancel_button.setEnabled(running)

    def clear(self):
        self.controller.cleanup()
        self.controller.set_project(None)
        for edit in (
            self.book, self.portrait, self.voice, self.sadtalker,
            self.output_directory, self.work_directory
        ):
            edit.clear()
        self.transcript.clear()
        self.rights.setChecked(False)
        self.preview_text.clear()
        self.progress.setValue(0)
        self.status.setText("Open a project and select the required inputs.")
        self.refresh()

    def dispose(self):
        self.clear()
