from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from backend.project.manager import ProjectManager


class ProjectController(QObject):
    """
    Connects the desktop UI layer with backend ProjectManager.

    Milestone 10.5 improvements:
    - clear signal handling
    - centralized project lifecycle
    - safer state access
    - consistent controller responsibility
    """

    projectOpened = Signal(Path)

    projectClosed = Signal()

    projectSaved = Signal(Path)

    projectModified = Signal(bool)


    def __init__(
        self,
    ):

        super().__init__()

        self.manager = ProjectManager()


    # --------------------------------------------------
    # Properties
    # --------------------------------------------------

    @property
    def current(
        self,
    ):

        return self.manager.current


    @property
    def project_root(
        self,
    ):

        if not self.manager.current:

            return None

        return self.manager.project_root()


    def has_project(
        self,
    ) -> bool:

        return self.manager.has_project()


    def is_modified(
        self,
    ) -> bool:

        project = self.manager.current

        if not project:

            return False

        return getattr(
            project,
            "modified",
            False,
        )


    # --------------------------------------------------
    # Project Creation
    # --------------------------------------------------

    def create_project(
        self,
        name: str,
        root: Path,
    ):

        project = self.manager.create(
            name,
            root,
        )

        self.projectOpened.emit(
            project.root
        )

        return project