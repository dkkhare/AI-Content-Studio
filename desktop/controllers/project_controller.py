from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from backend.project.manager import ProjectManager


class ProjectController(QObject):
    """
    Connects the desktop UI layer with the backend
    ProjectManager.

    Responsibilities:
    - Create projects
    - Open projects
    - Save projects
    - Close projects
    - Notify UI about project state changes

    Business logic remains inside ProjectManager.
    """

    projectOpened = Signal(Path)

    projectClosed = Signal()

    projectSaved = Signal(Path)

    projectModified = Signal(bool)


    def __init__(
        self,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.manager = ProjectManager()

        self._modified = False


    # --------------------------------------------------
    # Properties
    # --------------------------------------------------

    @property
    def current(self):

        return self.manager.current


    @property
    def modified(self):

        return self._modified


    def has_project(
        self,
    ) -> bool:

        return self.manager.has_project()


    def project_root(
        self,
    ) -> Path | None:

        if not self.has_project():

            return None

        return self.manager.project_root()


    # --------------------------------------------------
    # Internal State
    # --------------------------------------------------

    def mark_modified(
        self,
        value: bool = True,
    ):

        if self._modified != value:

            self._modified = value

            self.projectModified.emit(
                value
            )


    def reset_modified(
        self,
    ):

        self.mark_modified(
            False
        )
    # --------------------------------------------------
    # Project Creation
    # --------------------------------------------------

    def create_project(
        self,
        path: str | Path,
    ):

        project_path = Path(
            path
        )

        if not project_path:

            raise ValueError(
                "Project path is required"
            )


        if project_path.exists() and any(
            project_path.iterdir()
        ):

            raise FileExistsError(
                "Project directory is not empty"
            )


        try:

            project = (
                self.manager.create_project(
                    project_path
                )
            )


            self.manager.set_current(
                project
            )


            self.reset_modified()


            self.projectOpened.emit(
                project_path
            )


            return project


        except Exception:

            raise


    # --------------------------------------------------
    # Project Opening
    # --------------------------------------------------

    def open_project(
        self,
        path: str | Path,
    ):

        project_path = Path(
            path
        )


        if not project_path.exists():

            raise FileNotFoundError(
                f"Project not found: {project_path}"
            )


        try:

            project = (
                self.manager.load_project(
                    project_path
                )
            )


            self.manager.set_current(
                project
            )


            self.reset_modified()


            self.projectOpened.emit(
                project_path
            )


            return project


        except Exception:

            raise


    # --------------------------------------------------
    # Project Reload
    # --------------------------------------------------

    def reload_project(
        self,
    ):

        root = self.project_root()


        if not root:

            raise RuntimeError(
                "No project is open"
            )


        return self.open_project(
            root
        )
    # --------------------------------------------------
    # Save Project
    # --------------------------------------------------

    def save_project(
        self,
    ):

        if not self.has_project():

            raise RuntimeError(
                "No project is open"
            )


        try:

            self.manager.save_current()


            self.reset_modified()


            root = self.project_root()


            if root:

                self.projectSaved.emit(
                    root
                )


            return True


        except Exception:

            raise


    # --------------------------------------------------
    # Save Project As
    # --------------------------------------------------

    def save_project_as(
        self,
        path: str | Path,
    ):

        if not self.has_project():

            raise RuntimeError(
                "No project is open"
            )


        target = Path(
            path
        )


        if not target:

            raise ValueError(
                "Target path required"
            )


        try:

            self.manager.save_as(
                target
            )


            self.reset_modified()


            self.projectSaved.emit(
                target
            )


            return True


        except Exception:

            raise


    # --------------------------------------------------
    # Close Project
    # --------------------------------------------------

    def close_project(
        self,
        force: bool = False,
    ):

        if not self.has_project():

            return


        if self.modified and not force:

            raise RuntimeError(
                "Project has unsaved changes"
            )


        try:

            self.manager.close_current()


            self.reset_modified()


            self.projectClosed.emit()


        except Exception:

            raise


    # --------------------------------------------------
    # Unsaved Changes
    # --------------------------------------------------

    def has_unsaved_changes(
        self,
    ) -> bool:

        return self.modified


    def can_close(
        self,
    ) -> bool:

        return not self.has_unsaved_changes()
    # --------------------------------------------------
    # Project State Helpers
    # --------------------------------------------------

    def current_project(
        self,
    ):

        return self.manager.current


    def project_name(
        self,
    ) -> str | None:

        project = self.current_project()

        if not project:

            return None


        return getattr(
            project,
            "name",
            None,
        )


    def is_open(
        self,
    ) -> bool:

        return (
            self.manager.current
            is not None
        )


    def has_unsaved_changes(
        self,
    ) -> bool:

        return self._modified


    # --------------------------------------------------
    # Project Validation
    # --------------------------------------------------

    def validate_project(
        self,
    ) -> bool:

        if not self.is_open():

            return False


        return self.manager.validate_current()


    # --------------------------------------------------
    # Refresh
    # --------------------------------------------------

    def refresh(
        self,
    ):

        if not self.is_open():

            return


        self.manager.refresh()


    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def dispose(
        self,
    ):

        try:

            self.close_project()


        finally:

            self.manager = None