from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
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
    """Collect inputs and queue options for the configured project pipeline."""

    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project
        self._images: list[str] = []
        self.setWindowTitle("Queue Processing")
        self.setMinimumWidth(560)

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(
                "Select the page/image files to use for OCR and video rendering. "
                "Enabled stages are read from Project Settings."
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

    def _refresh_summary(self) -> None:
        project = self.project
        stages = []
        if project.get_setting("pipeline_ocr_enabled", True):
            stages.append(f"OCR ({project.get_setting('ocr_provider', 'paddle')})")
        if project.get_setting("pipeline_translation_enabled", False):
            stages.append("Translation")
        if project.get_setting("pipeline_narration_enabled", True):
            stages.append("Narration / TTS")
        if project.get_setting("pipeline_video_enabled", False):
            stages.append("Video Render")
        self.summary.setText("Configured stages: " + (" → ".join(stages) if stages else "None"))

    def data(self) -> dict:
        return {
            "ocr_images": list(self._images),
            "video_images": list(self._images),
        }

    def queue_priority(self) -> int:
        return int(self.priority.value())
