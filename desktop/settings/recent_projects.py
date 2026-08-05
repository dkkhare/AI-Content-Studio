from __future__ import annotations

from pathlib import Path

from .settings_manager import SettingsManager


class RecentProjects:
    """
    Maintains the recent project list.
    """

    SETTINGS_KEY = "recent/projects"

    def __init__(self):

        self.settings = SettingsManager()

    # --------------------------------------------------
    # Access
    # --------------------------------------------------

    def projects(self):

        return list(

            self.settings.value(

                self.SETTINGS_KEY,

                [],

            )

        )

    def add(

        self,

        project_path,

        limit=10,

    ):

        project_path = str(

            Path(project_path)

        )

        projects = self.projects()

        if project_path in projects:

            projects.remove(

                project_path

            )

        projects.insert(

            0,

            project_path,

        )

        self.settings.set_value(

            self.SETTINGS_KEY,

            projects[:limit],

        )

        self.settings.sync()

    def remove(

        self,

        project_path,

    ):

        projects = self.projects()

        if project_path in projects:

            projects.remove(

                project_path

            )

            self.settings.set_value(

                self.SETTINGS_KEY,

                projects,

            )

            self.settings.sync()

    def clear(self):

        self.settings.remove(

            self.SETTINGS_KEY

        )

        self.settings.sync()

    def latest(self):

        projects = self.projects()

        if projects:

            return projects[0]

        return None