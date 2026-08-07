from __future__ import annotations

from pathlib import Path

from .settings_manager import SettingsManager


class RecentProjects:
    """Persistent recent-project list backed by QSettings."""

    SETTINGS_KEY = "recent/projects"
    DEFAULT_LIMIT = 10

    def __init__(self):
        self.settings = SettingsManager()

    def projects(self) -> list[str]:
        value = self.settings.value(self.SETTINGS_KEY, [])

        if value is None:
            return []
        if isinstance(value, str):
            value = [value]

        return [str(Path(item)) for item in value if item]

    def get_all(self) -> list[str]:
        """Compatibility alias used by MainWindow."""
        return self.projects()

    def add(self, project_path, limit: int | None = None) -> None:
        project = str(Path(project_path).resolve())
        projects = self.projects()

        if project in projects:
            projects.remove(project)

        projects.insert(0, project)
        max_items = self.DEFAULT_LIMIT if limit is None else max(1, int(limit))

        self.settings.set_value(self.SETTINGS_KEY, projects[:max_items])
        self.settings.sync()

    def remove(self, project_path) -> None:
        project = str(Path(project_path).resolve())
        projects = [item for item in self.projects() if item != project]
        self.settings.set_value(self.SETTINGS_KEY, projects)
        self.settings.sync()

    def clear(self) -> None:
        self.settings.remove(self.SETTINGS_KEY)
        self.settings.sync()

    def latest(self) -> str | None:
        projects = self.projects()
        return projects[0] if projects else None
