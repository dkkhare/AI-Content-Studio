from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
)


class ProjectSettingsDialog(QDialog):
    """Edit project-specific settings persisted in project.json."""

    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project
        self.setWindowTitle("Project Settings")
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        form = QFormLayout()

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

        form.addRow("Language", self.language)
        form.addRow("Voice", self.voice)
        form.addRow("Output directory", self.output_directory)
        form.addRow("Autosave enabled", self.auto_save)
        form.addRow("Autosave interval", self.autosave_interval)
        form.addRow("Backup retention", self.backup_retention)
        form.addRow("Theme", self.theme)
        layout.addLayout(form)

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
            },
        }
