from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
)


class ProjectSettingsDialog(QDialog):
    """Edit project-specific lifecycle and processing settings."""

    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project
        self.setWindowTitle("Project Settings")
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)

        general_group = QGroupBox("General", self)
        general = QFormLayout(general_group)

        self.language = QLineEdit(project.language, self)
        self.voice = QLineEdit(project.voice, self)
        self.output_directory = QLineEdit(project.output_directory, self)

        self.auto_save = QCheckBox(self)
        self.auto_save.setChecked(bool(project.auto_save))

        self.autosave_interval = QSpinBox(self)
        self.autosave_interval.setRange(10, 3600)
        self.autosave_interval.setSuffix(" seconds")
        self.autosave_interval.setValue(
            int(project.get_setting("autosave_interval_seconds", 300))
        )

        self.backup_retention = QSpinBox(self)
        self.backup_retention.setRange(0, 100)
        self.backup_retention.setValue(
            int(project.get_setting("backup_retention", 10))
        )

        self.theme = QComboBox(self)
        self.theme.addItems(["dark", "light", "system"])
        theme = str(project.get_setting("theme", "dark"))
        index = self.theme.findText(theme)
        if index >= 0:
            self.theme.setCurrentIndex(index)

        general.addRow("Language", self.language)
        general.addRow("Voice", self.voice)
        general.addRow("Output directory", self.output_directory)
        general.addRow("Autosave enabled", self.auto_save)
        general.addRow("Autosave interval", self.autosave_interval)
        general.addRow("Backup retention", self.backup_retention)
        general.addRow("Theme", self.theme)
        layout.addWidget(general_group)

        processing_group = QGroupBox("Processing Pipeline", self)
        processing = QFormLayout(processing_group)

        self.ocr_enabled = QCheckBox(self)
        self.ocr_enabled.setChecked(bool(project.get_setting("pipeline_ocr_enabled", True)))
        self.ocr_provider = QComboBox(self)
        self.ocr_provider.addItems(["paddle", "tesseract", "easyocr"])
        provider = str(project.get_setting("ocr_provider", "paddle"))
        provider_index = self.ocr_provider.findText(provider)
        if provider_index >= 0:
            self.ocr_provider.setCurrentIndex(provider_index)

        self.translation_enabled = QCheckBox(self)
        self.translation_enabled.setChecked(
            bool(project.get_setting("pipeline_translation_enabled", False))
        )
        self.translation_provider = QComboBox(self)
        self.translation_provider.addItems(["google"])
        translation_provider = str(project.get_setting("translation_provider", "google"))
        translation_provider_index = self.translation_provider.findText(translation_provider)
        if translation_provider_index >= 0:
            self.translation_provider.setCurrentIndex(translation_provider_index)

        self.translation_api_key_env = QLineEdit(
            str(project.get_setting("translation_api_key_env", "GOOGLE_TRANSLATE_API_KEY")),
            self,
        )
        self.translation_api_key_env.setPlaceholderText("Environment variable containing API key")
        self.translation_source = QLineEdit(
            str(project.get_setting("translation_source_language", project.language)), self
        )
        self.translation_target = QLineEdit(
            str(project.get_setting("translation_target_language", project.language)), self
        )

        self.narration_enabled = QCheckBox(self)
        self.narration_enabled.setChecked(
            bool(project.get_setting("pipeline_narration_enabled", True))
        )

        self.video_enabled = QCheckBox(self)
        self.video_enabled.setChecked(
            bool(project.get_setting("pipeline_video_enabled", False))
        )
        self.video_fps = QSpinBox(self)
        self.video_fps.setRange(1, 120)
        self.video_fps.setValue(int(project.get_setting("video_fps", 30)))

        self.video_seconds_per_image = QDoubleSpinBox(self)
        self.video_seconds_per_image.setRange(0.1, 60.0)
        self.video_seconds_per_image.setDecimals(1)
        self.video_seconds_per_image.setSingleStep(0.5)
        self.video_seconds_per_image.setSuffix(" seconds")
        self.video_seconds_per_image.setValue(
            float(project.get_setting("video_seconds_per_image", 3.0))
        )

        self.ffmpeg_path = QLineEdit(str(project.get_setting("ffmpeg_path", "")), self)
        self.ffmpeg_path.setPlaceholderText("Leave blank to use ffmpeg from PATH")

        processing.addRow("OCR enabled", self.ocr_enabled)
        processing.addRow("OCR provider", self.ocr_provider)
        processing.addRow("Translation enabled", self.translation_enabled)
        processing.addRow("Translation provider", self.translation_provider)
        processing.addRow("Translation API key env", self.translation_api_key_env)
        processing.addRow("Translation source", self.translation_source)
        processing.addRow("Translation target", self.translation_target)
        processing.addRow("Narration/TTS enabled", self.narration_enabled)
        processing.addRow("Video rendering enabled", self.video_enabled)
        processing.addRow("Video FPS", self.video_fps)
        processing.addRow("Seconds per image", self.video_seconds_per_image)
        processing.addRow("FFmpeg path", self.ffmpeg_path)
        layout.addWidget(processing_group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self) -> dict:
        output_directory = self.output_directory.text().strip() or "output"
        return {
            "language": self.language.text().strip() or "en",
            "voice": self.voice.text().strip(),
            "output_directory": output_directory,
            "auto_save": self.auto_save.isChecked(),
            "settings": {
                "autosave_interval_seconds": self.autosave_interval.value(),
                "backup_retention": self.backup_retention.value(),
                "theme": self.theme.currentText(),
                "pipeline_ocr_enabled": self.ocr_enabled.isChecked(),
                "ocr_provider": self.ocr_provider.currentText(),
                "pipeline_translation_enabled": self.translation_enabled.isChecked(),
                "translation_provider": self.translation_provider.currentText(),
                "translation_api_key_env": (
                    self.translation_api_key_env.text().strip()
                    or "GOOGLE_TRANSLATE_API_KEY"
                ),
                "translation_source_language": self.translation_source.text().strip() or "en",
                "translation_target_language": self.translation_target.text().strip() or "en",
                "pipeline_narration_enabled": self.narration_enabled.isChecked(),
                "pipeline_video_enabled": self.video_enabled.isChecked(),
                "video_fps": self.video_fps.value(),
                "video_seconds_per_image": self.video_seconds_per_image.value(),
                "ffmpeg_path": self.ffmpeg_path.text().strip(),
            },
        }
