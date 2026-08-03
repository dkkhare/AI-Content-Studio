from pathlib import Path

from PySide6.QtCore import QObject, Signal


class ProjectController(QObject):
    """
    Controls the currently opened project.
    """

    projectOpened = Signal(Path)

    projectClosed = Signal()

    projectSaved = Signal(Path)

    def __init__(self):

        super().__init__()

        self.project_path = None

    def new_project(self):

        self.project_path = None

    def open_project(self, path: Path):

        self.project_path = path

        self.projectOpened.emit(path)

    def save_project(self):

        if self.project_path:

            self.projectSaved.emit(self.project_path)

    def close_project(self):

        self.project_path = None

        self.projectClosed.emit()