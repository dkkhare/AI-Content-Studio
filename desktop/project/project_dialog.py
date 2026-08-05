from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QInputDialog,
)


class ProjectDialogs:

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

        return (
            name.strip(),
            Path(directory) / name.strip(),
        )

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