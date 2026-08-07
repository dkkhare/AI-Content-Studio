from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QInputDialog,
    QMessageBox,
)


class ProjectDialogs:
    """Dialog helpers for project lifecycle actions."""

    @staticmethod
    def new_project(parent):
        name, ok = QInputDialog.getText(
            parent,
            "New Project",
            "Project name:",
        )

        if not ok or not name.strip():
            return None

        directory = QFileDialog.getExistingDirectory(
            parent,
            "Choose Project Location",
        )

        if not directory:
            return None

        name = name.strip()
        return name, Path(directory) / name

    @staticmethod
    def open_project(parent):
        directory = QFileDialog.getExistingDirectory(
            parent,
            "Open Project",
        )

        if not directory:
            return None

        return Path(directory)

    @staticmethod
    def save_project_as(parent):
        directory = QFileDialog.getExistingDirectory(
            parent,
            "Save Project As",
        )

        if not directory:
            return None

        return Path(directory)

    @staticmethod
    def confirm_close(parent) -> str:
        """Return one of: 'save', 'discard', or 'cancel'."""
        result = QMessageBox.warning(
            parent,
            "Unsaved Changes",
            "This project has unsaved changes. Save before closing?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save,
        )

        if result == QMessageBox.Save:
            return "save"
        if result == QMessageBox.Discard:
            return "discard"
        return "cancel"

    # Compatibility aliases for older callers.
    create_project = new_project
    save_as_project = save_project_as
