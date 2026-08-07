from __future__ import annotations

from pathlib import Path

from .settings_manager import SettingsManager


class RecentProjects:
    """Persistent recent-project list with pinning and stale-path cleanup."""

    SETTINGS_KEY = "recent/projects"
    PINNED_KEY = "recent/pinned"
    LIMIT_KEY = "recent/limit"
    DEFAULT_LIMIT = 10

    def __init__(self):
        self.settings = SettingsManager()

    def _list_value(self, key: str) -> list[str]:
        value = self.settings.value(key, [])
        if value is None:
            return []
        if isinstance(value, str):
            value = [value]
        return [str(Path(item)) for item in value if item]

    def limit(self) -> int:
        try:
            return max(1, int(self.settings.value(self.LIMIT_KEY, self.DEFAULT_LIMIT)))
        except (TypeError, ValueError):
            return self.DEFAULT_LIMIT

    def set_limit(self, value: int) -> None:
        value = max(1, int(value))
        self.settings.set_value(self.LIMIT_KEY, value)
        self.settings.set_value(self.SETTINGS_KEY, self.projects()[:value])
        self.settings.sync()

    def pinned(self) -> list[str]:
        return self._list_value(self.PINNED_KEY)

    def is_pinned(self, project_path) -> bool:
        project = str(Path(project_path).resolve())
        return project in self.pinned()

    def pin(self, project_path) -> None:
        project = str(Path(project_path).resolve())
        pinned = [item for item in self.pinned() if item != project]
        pinned.insert(0, project)
        self.settings.set_value(self.PINNED_KEY, pinned)
        self.add(project)

    def unpin(self, project_path) -> None:
        project = str(Path(project_path).resolve())
        pinned = [item for item in self.pinned() if item != project]
        self.settings.set_value(self.PINNED_KEY, pinned)
        self.settings.sync()

    def projects(self) -> list[str]:
        projects = self._list_value(self.SETTINGS_KEY)
        pinned = [item for item in self.pinned() if item in projects]
        normal = [item for item in projects if item not in pinned]
        return (pinned + normal)[: self.limit()]

    def get_all(self) -> list[str]:
        return self.projects()

    def add(self, project_path, limit: int | None = None) -> None:
        project = str(Path(project_path).resolve())
        projects = [item for item in self._list_value(self.SETTINGS_KEY) if item != project]
        projects.insert(0, project)

        max_items = self.limit() if limit is None else max(1, int(limit))
        pinned = [item for item in self.pinned() if item in projects]
        normal = [item for item in projects if item not in pinned]
        ordered = (pinned + normal)[:max_items]

        self.settings.set_value(self.SETTINGS_KEY, ordered)
        self.settings.sync()

    def remove(self, project_path) -> None:
        project = str(Path(project_path).resolve())
        projects = [item for item in self._list_value(self.SETTINGS_KEY) if item != project]
        pinned = [item for item in self.pinned() if item != project]
        self.settings.set_value(self.SETTINGS_KEY, projects)
        self.settings.set_value(self.PINNED_KEY, pinned)
        self.settings.sync()

    def remove_missing(self) -> list[str]:
        removed = []
        for item in list(self._list_value(self.SETTINGS_KEY)):
            path = Path(item)
            if not path.exists() or not path.is_dir():
                removed.append(item)
                self.remove(item)
        return removed

    def clear(self) -> None:
        self.settings.remove(self.SETTINGS_KEY)
        self.settings.remove(self.PINNED_KEY)
        self.settings.sync()

    def latest(self) -> str | None:
        projects = self.projects()
        return projects[0] if projects else None
