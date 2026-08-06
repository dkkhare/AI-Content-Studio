from pathlib import Path

from PySide6.QtCore import QObject, Signal


from backend.project.manager import ProjectManager


class ProjectController(QObject):

    projectOpened = Signal(object)

    projectClosed = Signal()

    projectSaved = Signal()

    projectModified = Signal()


    def __init__(
        self,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.project = None

        self.project_manager = (
            ProjectManager()
        )

        self.project_path = None

        self.modified = False


    # --------------------------------------------------
    # Factory Methods
    # --------------------------------------------------

    @classmethod
    def create(
        cls,
        path,
        parent=None,
    ):

        controller = cls(
            parent
        )

        controller.project_path = (
            Path(path)
        )

        controller.project = (
            controller.project_manager.create_project(
                controller.project_path
            )
        )

        return controller


    @classmethod
    def open(
        cls,
        path,
        parent=None,
    ):

        controller = cls(
            parent
        )

        controller.project_path = (
            Path(path)
        )

        controller.project = (
            controller.project_manager.load_project(
                controller.project_path
            )
        )

        return controller


    # --------------------------------------------------
    # Lifecycle
    # --------------------------------------------------

    def open_project(
        self,
    ):

        if not self.project:

            raise RuntimeError(
                "No project loaded"
            )


        self.modified = False

        self.projectOpened.emit(
            self.project_path
        )


    def close(
        self,
    ):

        self.project = None

        self.project_path = None

        self.modified = False

        self.projectClosed.emit()


    # --------------------------------------------------
    # State
    # --------------------------------------------------

    def mark_modified(
        self,
    ):

        if not self.modified:

            self.modified = True

            self.projectModified.emit()