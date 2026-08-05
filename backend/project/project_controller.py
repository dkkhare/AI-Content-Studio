from __future__ import annotations

from pathlib import Path

from backend.project import ProjectManager


class ProjectController:
    """
    Desktop wrapper around ProjectManager.
    """

    def __init__(self):

        self.manager = ProjectManager()

    # --------------------------------------------------
    # Create
    # --------------------------------------------------

    def create_project(

        self,

        name: str,

        directory,

    ):

        return self.manager.create(

            name,

            Path(directory),

        )

    # --------------------------------------------------
    # Open
    # --------------------------------------------------

    def open_project(

        self,

        directory,

    ):

        return self.manager.open(

            Path(directory),

        )

    # --------------------------------------------------
    # Save
    # --------------------------------------------------

    def save_project(self):

        return self.manager.save()

    def save_project_as(

        self,

        directory,

    ):

        return self.manager.save_as(

            Path(directory),

        )

    # --------------------------------------------------
    # Close
    # --------------------------------------------------

    def close_project(self):

        self.manager.close()

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    @property
    def current(self):

        return self.manager.current

    def has_project(self):

        return self.manager.has_project()

    def auto_save(self):

        return self.manager.auto_save()