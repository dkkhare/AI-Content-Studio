from __future__ import annotations

from pathlib import Path

from backend.project.exceptions import (
    ProjectExistsError,
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
    Create/Open/Save AI Content Studio projects.
    """

    def __init__(self):

        self.project = None

    # --------------------------------------------------
    # Properties
    # --------------------------------------------------

    @property
    def current(self):

        return self.project

    def has_project(self):

        return self.project is not None

    # --------------------------------------------------
    # Create
    # --------------------------------------------------

    def create(

        self,

        name,

        root,

    ):

        root = Path(root)

        if root.exists() and (
            root / "project.json"
        ).exists():

            raise ProjectExistsError(
                "Project already exists."
            )

        project = Project(
            name=name,
            root=root,
        )

        project.create_directories()

        ProjectSerializer.save(
            project
        )

        self.project = project

        return project

    # --------------------------------------------------
    # Open
    # --------------------------------------------------

    def open(

        self,

        root,

    ):

        root = Path(root)

        ProjectValidator.validate(root)

        project = ProjectSerializer.load(root)

        if not project.is_version_supported():

            raise RuntimeError(
                f"Unsupported project version: {project.version}"
            )

        self.project = project

        return self.project

    # --------------------------------------------------
    # Save
    # --------------------------------------------------

    def save(self):

        if not self.has_project():

            return False

        ProjectSerializer.save(
            self.project
        )

        return True

    # --------------------------------------------------
    # Save As
    # --------------------------------------------------

    def save_as(

        self,

        new_root,

    ):

        if not self.has_project():

            return False

        self.project.root = Path(new_root)

        self.project.create_directories()

        self.save()

        return True

    # --------------------------------------------------
    # Close
    # --------------------------------------------------

    def close(self):

        self.project = None

    # --------------------------------------------------
    # Auto Save
    # --------------------------------------------------

    def auto_save(self):

        if not self.has_project():

            return False

        if not self.project.auto_save:

            return False

        self.save()

        return True

    # --------------------------------------------------
    # Status
    # --------------------------------------------------

    def project_name(self):

        if not self.has_project():

            return ""

        return self.project.name

    def project_root(self):

        if not self.has_project():

            return None

        return self.project.root

    def project_file(self):

        if not self.has_project():

            return None

        return self.project.project_file

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def touch(self):

        if self.has_project():

            self.project.touch()

    def exists(self):

        if not self.has_project():

            return False

        return self.project.exists()

    def refresh(self):

        if not self.has_project():

            return None

        self.project = ProjectSerializer.load(
            self.project.root
        )

        return self.project

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------

    def validate(self):

        if not self.has_project():

            return False

        return ProjectValidator.validate(
            self.project.root
        )

    # --------------------------------------------------
    # Information
    # --------------------------------------------------

    def project_metadata(self):

        if not self.has_project():

            return {}

        return self.project.metadata

    def project_version(self):

        if not self.has_project():

            return ""

        return self.project.version

    def is_supported(self):

        if not self.has_project():

            return False

        return self.project.is_version_supported()