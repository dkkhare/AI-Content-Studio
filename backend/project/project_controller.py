from __future__ import annotations

from pathlib import Path

from backend.project.manager import ProjectManager


class ProjectController:
    """Compatibility wrapper around ProjectManager for non-Qt callers."""

    def __init__(self):
        self.manager = ProjectManager()

    def create_project(self, name: str, directory) -> object:
        return self.manager.create_project(
            path=Path(directory),
            name=name,
        )

    def open_project(self, directory):
        return self.manager.load_project(
            Path(directory)
        )

    def save_project(self) -> bool:
        return self.manager.save_current()

    def save_project_as(self, directory):
        return self.manager.save_as(
            Path(directory)
        )

    def close_project(self, force: bool = False) -> bool:
        return self.manager.close_current(
            force=force
        )

    def refresh(self):
        return self.manager.reload_current()

    @property
    def current(self):
        return self.manager.current

    def has_project(self) -> bool:
        return self.manager.has_project()

    def auto_save(self):
        return self.manager.autosave()

    def has_recovery(self) -> bool:
        return self.manager.has_recovery()

    def recover(self):
        return self.manager.recover()
