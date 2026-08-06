from __future__ import annotations

from pathlib import Path

from backend.project.exceptions import (
    ProjectExistsError,
    ProjectNotFoundError,
)

from backend.project.project import Project

from backend.project.serializer import (
    ProjectSerializer,
)

from backend.project.validator import (
    ProjectValidator,
)



class ProjectManager:
    """
    Central backend service for project lifecycle.

    Responsibilities:
    - Create projects
    - Open projects
    - Save projects
    - Close projects
    - Track current project state

    UI logic must not exist here.
    """


    def __init__(
        self,
    ):

        self.project: Project | None = None

        self.modified: bool = False



    # --------------------------------------------------
    # Properties
    # --------------------------------------------------

    @property
    def current(
        self,
    ) -> Project | None:

        return self.project



    def has_project(
        self,
    ) -> bool:

        return (
            self.project is not None
        )



    def project_root(
        self,
    ) -> Path | None:

        if not self.project:

            return None


        return self.project.root



    # --------------------------------------------------
    # State Management
    # --------------------------------------------------

    def set_current(
        self,
        project: Project,
    ):

        self.project = project

        self.modified = False



    def mark_modified(
        self,
    ):

        self.modified = True



    def clear_modified(
        self,
    ):

        self.modified = False



    def has_changes(
        self,
    ) -> bool:

        return self.modified
    # --------------------------------------------------
    # Create Project
    # --------------------------------------------------

    def create_project(
        self,
        path: str | Path,
    ) -> Project:

        project_path = Path(
            path
        )


        if project_path.exists():

            if any(
                project_path.iterdir()
            ):

                raise ProjectExistsError(
                    "Project directory already exists and is not empty"
                )


        else:

            project_path.mkdir(
                parents=True,
                exist_ok=True,
            )


        project = Project(
            root=project_path
        )


        ProjectValidator.validate_structure(
            project
        )


        ProjectSerializer.save(
            project
        )


        self.set_current(
            project
        )


        return project



    # --------------------------------------------------
    # Load Project
    # --------------------------------------------------

    def load_project(
        self,
        path: str | Path,
    ) -> Project:

        project_path = Path(
            path
        )


        if not project_path.exists():

            raise ProjectNotFoundError(
                f"Project not found: {project_path}"
            )


        project = (
            ProjectSerializer.load(
                project_path
            )
        )


        ProjectValidator.validate_structure(
            project
        )


        self.set_current(
            project
        )


        return project



    # --------------------------------------------------
    # Validation
    # --------------------------------------------------

    def validate_current(
        self,
    ) -> bool:

        if not self.project:

            return False


        return (
            ProjectValidator.validate_structure(
                self.project
            )
        )
    # --------------------------------------------------
    # Save Project
    # --------------------------------------------------

    def save_project(
        self,
    ):

        if not self.project:

            raise RuntimeError(
                "No project is currently open"
            )


        ProjectSerializer.save(
            self.project
        )


        self.clear_modified()



    # --------------------------------------------------
    # Save As
    # --------------------------------------------------

    def save_as(
        self,
        path: str | Path,
    ):

        if not self.project:

            raise RuntimeError(
                "No project is currently open"
            )


        new_path = Path(
            path
        )


        new_path.mkdir(
            parents=True,
            exist_ok=True,
        )


        self.project.root = (
            new_path
        )


        ProjectValidator.validate_structure(
            self.project
        )


        ProjectSerializer.save(
            self.project
        )


        self.clear_modified()


        return self.project



    # --------------------------------------------------
    # Close Project
    # --------------------------------------------------

    def close_project(
        self,
    ):

        if not self.project:

            return


        self.project = None


        self.clear_modified()



    # --------------------------------------------------
    # Refresh Project
    # --------------------------------------------------

    def refresh(
        self,
    ):

        if not self.project:

            return None


        self.project = (
            ProjectSerializer.load(
                self.project.root
            )
        )


        self.clear_modified()


        return self.project
    # --------------------------------------------------
    # Refresh Current Project
    # --------------------------------------------------

    def refresh(
        self,
    ):

        if not self.project:

            return None


        ProjectValidator.validate_structure(
            self.project
        )


        return self.project



    # --------------------------------------------------
    # Reload Current Project
    # --------------------------------------------------

    def reload(
        self,
    ):

        if not self.project:

            raise ProjectNotFoundError(
                "No project is currently open"
            )


        root = self.project.root


        project = (
            ProjectSerializer.load(
                root
            )
        )


        self.set_current(
            project
        )


        return project



    # --------------------------------------------------
    # Project Information
    # --------------------------------------------------

    def project_name(
        self,
    ) -> str | None:

        if not self.project:

            return None


        return getattr(
            self.project,
            "name",
            None,
        )



    def project_exists(
        self,
        path: str | Path,
    ) -> bool:

        project_path = Path(
            path
        )


        return (
            project_path.exists()
            and
            project_path.is_dir()
        )



    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def dispose(
        self,
    ):

        try:

            if self.project:

                self.close_project()


        finally:

            self.project = None

            self.modified = False