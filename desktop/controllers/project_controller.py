from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from backend.project.manager import ProjectManager


class ProjectController(QObject):
    """
    Connects the UI with the backend ProjectManager.
    """

    projectOpened = Signal(Path)

    projectClosed = Signal()

    projectSaved = Signal(Path)

    projectModified = Signal(bool)

    def __init__(self):

        super().__init__()

        self.manager = ProjectManager()

    # --------------------------------------------------
    # Properties
    # --------------------------------------------------

    @property
    def current(self):

        return self.manager.current

    def has_project(self):

        return self.manager.has_project()

    # --------------------------------------------------
    # Project Operations
    # --------------------------------------------------

    def create_project(

        self,

        name,

        root,

    ):

        project = self.manager.create(

            name,

            root,

        )

        self.projectOpened.emit(

            project.root

        )

        return project

    def open_project(

        self,

        root,

    ):

        project = self.manager.open(

            root,

        )

        self.projectOpened.emit(

            project.root

        )

        return project

    def save_project(self):

        if self.manager.save():

            self.projectSaved.emit(

                self.manager.project_root()

            )

            return True

        return False

    def save_project_as(

        self,

        root,

    ):

        return self.manager.save_as(

            root,

        )

    def close_project(self):

        self.manager.close()

        self.projectClosed.emit()

    def auto_save(self):

        return self.manager.auto_save()

    # --------------------------------------------------
    # Dirty State
    # --------------------------------------------------

    def set_modified(

        self,

        modified=True,

    ):

        self.manager.set_modified(

            modified,

        )

        self.projectModified.emit(

            self.manager.is_modified()

        )

    def clear_modified(self):

        self.manager.clear_modified()

        self.projectModified.emit(False)

    def is_modified(self):

        return self.manager.is_modified()

    # --------------------------------------------------
    # Information
    # --------------------------------------------------

    def project(self):

        return self.manager.current

    def project_name(self):

        return self.manager.project_name()

    def project_root(self):

        return self.manager.project_root()

    def project_file(self):

        return self.manager.project_file()

    def project_metadata(self):

        return self.manager.project_metadata()

    def statistics(self):

        return self.manager.statistics()

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------

    def validate(self):

        return self.manager.validate()

    def refresh(self):

        return self.manager.refresh()

    def exists(self):

        return self.manager.exists()

    def is_supported(self):

        return self.manager.is_supported()