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

    # --------------------------------------------------
    # Project Operations
    # --------------------------------------------------

    def new_project(self):

        self.project_path = None

    def open_project(self, path: Path):

        self.project_path = Path(path)

        self.projectOpened.emit(

            self.project_path

        )

    def save_project(self):

        if self.project_path is None:

            return

        self.projectSaved.emit(

            self.project_path

        )

    def close_project(self):

        self.project_path = None

        self.projectClosed.emit()

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def has_project(self):

        return self.project_path is not None

    def current_project(self):

        return self.project_path
    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def has_project(self):

        return self.project_path is not None

    def current_project(self):

        return self.project_path

    def project_name(self):

        if self.project_path is None:

            return None

        return self.project_path.name
    # --------------------------------------------------
    # Information
    # --------------------------------------------------

    def project_directory(self):

        return self.project_path

    def is_open(self):

        return self.project_path is not None