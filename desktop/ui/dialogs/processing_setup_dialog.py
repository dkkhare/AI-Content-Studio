from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)


class ProcessingSetupDialog(QDialog):
    """Collect inputs and per-run processing choices for the project pipeline."""

    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project
        self._images: list[str] = []
        self.setWindowTitle("Queue Processing")
        self.setMinimumWidth(600)

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(
                "Select the page/image files and choose optional Hindi proofreading steps. "
                "Spelling and grammar correction are independent and are never enabled silently."
            )
        )

        row = QHBoxLayout()
        self.images_edit = QLineEdit(self)
        self.images_edit.setReadOnly(True)
        self.images_edit.setPlaceholderText("No source images selected")
        browse = QPushButton("Browse Images...", self)
        browse.clicked.connect(self._browse_images)
        row.addWidget(self.images_edit, 1)
        row.addWidget(browse)
        layout.addLayout(row)

        options = QFormLayout()

        self.spelling_correction = QCheckBox("Correct Hindi spelling", self)
        self.spelling_correction.setChecked(
            bool(project.get_setting("pipeline_hindi_spelling_correction_enabled", False))
        )
        self.spelling_correction.setToolTip(
            "Correct spelling, matras and typographical errors only; do not rewrite grammar or style."
        )
        self.spelling_correction.toggled.connect(self._refresh_summary)
        options.addRow("Optional proofing", self.spelling_correction)

        self.grammar_correction = QCheckBox("Correct Hindi grammar", self)
        self.grammar_correction.setChecked(
            bool(project.get_setting("pipeline_hindi_grammar_correction_enabled", False))
        )
        self.grammar_correction.setToolTip(
            "Correct Hindi grammar after spelling correction when both options are selected."
        )
        self.grammar_correction.toggled.connect(self._refresh_summary)
        options.addRow("", self.grammar_correction)

        self.priority = QSpinBox(self)
        self.priority.setRange(-100, 100)
        self.priority.setValue(0)
        self.priority.setToolTip("Higher values are processed before lower-priority queued jobs.")
        options.addRow("Queue priority", self.priority)
        layout.addLayout(options)

        self.summary = QLabel(self)
        self.summary.setWordWrap(True)
        self._refresh_summary()
        layout.addWidget(self.summary)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            parent=self,
        )
        buttons.button(QDialogButtonBox.Ok).setText("Add to Queue")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_images(self) -> None:
        start = str(self.project.root if self.project is not None else Path.home())
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Source Images",
            start,
            "Images (*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff);;All Files (*)",
        )
        if files:
            self._images = files
            self.images_edit.setText(f"{len(files)} image(s) selected")

    def _refresh_summary(self, *_args) -> None:
        project = self.project
        stages = []
        if project.get_setting("pipeline_ocr_enabled", True):
            stages.append(f"OCR ({project.get_setting('ocr_provider', 'paddle')})")
        if project.get_setting("pipeline_ai_ocr_cleanup_enabled", False):
            stages.append("AI OCR Cleanup")
        if self.spelling_correction.isChecked():
            stages.append("Hindi Spelling Correction")
        if self.grammar_correction.isChecked():
            stages.append("Hindi Grammar Correction")
        if project.get_setting("pipeline_translation_enabled", False):
            stages.append("Translation")
        if project.get_setting("pipeline_ai_summary_enabled", False):
            stages.append("AI Summary")
        if project.get_setting("pipeline_ai_script_enabled", False):
            stages.append("Hindi Podcast Script")
        if project.get_setting("pipeline_ai_subtitle_enabled", False):
            stages.append("Hindi Subtitle Preparation")
        if project.get_setting("pipeline_narration_enabled", True):
            stages.append("F5-TTS Hindi Narration")
        if project.get_setting("pipeline_video_enabled", False):
            stages.append("Video Render")
        self.summary.setText("This run: " + (" → ".join(stages) if stages else "None"))

    def proofing_options(self) -> dict[str, bool]:
        return {
            "pipeline_hindi_spelling_correction_enabled": self.spelling_correction.isChecked(),
            "pipeline_hindi_grammar_correction_enabled": self.grammar_correction.isChecked(),
        }

    def accept(self) -> None:
        self.project.update_settings(self.proofing_options())
        super().accept()

    def data(self) -> dict:
        return {
            "ocr_images": list(self._images),
            "video_images": list(self._images),
        }

    def queue_priority(self) -> int:
        return int(self.priority.value())
