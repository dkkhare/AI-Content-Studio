from pathlib import Path

from PySide6.QtCore import QObject, Signal


class ProjectController(QObject):
    """
    Controls the currently opened project.
    """

    projectOpened = Signal(Path)

    projectClosed = Signal()

    projectSaved = Signal(Path)

    projectModified = Signal(bool)

    def __init__(self):

        super().__init__()

        self.project_path = None

        self.modified = False

    # --------------------------------------------------
    # Project Operations
    # --------------------------------------------------

    def new_project(self):

        self.project_path = None

        self.modified = False

    def open_project(self, path: Path):

        self.project_path = Path(path)

        self.modified = False

        self.projectOpened.emit(

            self.project_path

        )

    def save_project(self):

        if self.project_path is None:

            return

        self.clear_modified()

        self.projectSaved.emit(

            self.project_path

        )

    def close_project(self):

        self.project_path = None

        self.modified = False

        self.projectClosed.emit()

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

    # --------------------------------------------------
    # Dirty State
    # --------------------------------------------------

    def is_modified(self):

        return self.modified

    def set_modified(

        self,

        modified=True,

    ):

        modified = bool(modified)

        if self.modified == modified:

            return

        self.modified = modified

        self.projectModified.emit(

            modified

        )

    def clear_modified(self):

        self.set_modified(False)