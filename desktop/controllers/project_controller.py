from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Signal

from backend.project.manager import ProjectManager


class ProjectController(QObject):
    """Qt-facing controller for the project lifecycle."""

    projectOpened = Signal(object)
    projectClosed = Signal()
    projectSaved = Signal(object)
    projectModified = Signal(bool)
    projectAutoSaved = Signal(object)
    projectBackupCreated = Signal(object)
    projectBackupRestored = Signal(object)
    projectRecoveryAvailable = Signal(object)
    projectRecovered = Signal(object)
    projectSettingsChanged = Signal(dict)
    recentProjectsChanged = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = ProjectManager()
        self._modified = False
        self._recent_projects: list[Path] = []
        self._last_saved: datetime | None = None

        self._autosave_enabled = True
        self._autosave_interval = 5 * 60 * 1000
        self._autosave_timer = QTimer(self)
        self._autosave_timer.timeout.connect(self.auto_save)
        self._autosave_timer.start(self._autosave_interval)

    @property
    def current(self):
        return self.manager.current

    @property
    def project(self):
        return self.manager.current

    @property
    def modified(self) -> bool:
        return self._modified

    @property
    def autosave_enabled(self) -> bool:
        return self._autosave_enabled

    @property
    def recent_projects(self) -> list[Path]:
        return list(self._recent_projects)

    @property
    def last_saved(self) -> datetime | None:
        return self._last_saved

    def has_project(self) -> bool:
        return self.manager.has_project()

    def is_open(self) -> bool:
        return self.manager.is_open()

    def project_root(self) -> Path | None:
        return self.manager.project_root()

    def project_name(self) -> str | None:
        return self.manager.project_name()

    # --------------------------------------------------
    # Modified state
    # --------------------------------------------------

    def mark_modified(self, value: bool = True) -> None:
        value = bool(value)
        if value:
            self.manager.mark_modified()
        else:
            self.manager.clear_modified()

        if self._modified != value:
            self._modified = value
            self.projectModified.emit(value)

    def reset_modified(self) -> None:
        self.mark_modified(False)

    def sync_modified_state(self) -> None:
        value = bool(self.manager.modified)
        if self._modified != value:
            self._modified = value
            self.projectModified.emit(value)

    def has_unsaved_changes(self) -> bool:
        self.sync_modified_state()
        return self._modified

    def can_close(self) -> bool:
        return not self.has_unsaved_changes()

    # --------------------------------------------------
    # Autosave / recovery
    # --------------------------------------------------

    def enable_autosave(self, enabled: bool = True) -> None:
        self._autosave_enabled = bool(enabled)
        if self._autosave_enabled:
            self._autosave_timer.start(self._autosave_interval)
        else:
            self._autosave_timer.stop()

    def set_autosave_interval(self, milliseconds: int) -> None:
        self._autosave_interval = max(10_000, int(milliseconds))
        if self._autosave_enabled:
            self._autosave_timer.start(self._autosave_interval)

    def _apply_project_preferences(self) -> None:
        project = self.project
        if project is None:
            return

        seconds = int(project.get_setting("autosave_interval_seconds", 300))
        self.set_autosave_interval(max(10, seconds) * 1000)
        self.enable_autosave(bool(project.auto_save))

    def auto_save(self) -> bool:
        if not self._autosave_enabled or not self.has_project():
            return False
        self.sync_modified_state()
        if not self._modified:
            return False

        recovery = self.manager.autosave()
        if recovery is None:
            return False
        self.projectAutoSaved.emit(recovery)
        return True

    def has_recovery(self) -> bool:
        return self.manager.has_recovery() if self.has_project() else False

    def recovery_path(self) -> Path | None:
        return self.manager.recovery_path() if self.has_project() else None

    def load_recovery(self):
        return self.manager.load_recovery() if self.has_project() else None

    def recover_project(self) -> bool:
        if not self.has_project() or not self.manager.has_recovery():
            return False
        project = self.manager.recover()
        self._apply_project_preferences()
        self._modified = True
        self.projectModified.emit(True)
        self.projectRecovered.emit(project.root)
        return True

    def clear_recovery(self) -> bool:
        return self.manager.clear_recovery() if self.has_project() else False

    # --------------------------------------------------
    # Recent projects (session-level)
    # --------------------------------------------------

    def add_recent_project(self, path: str | Path) -> None:
        project_path = Path(path).resolve()
        self._recent_projects = [p for p in self._recent_projects if p != project_path]
        self._recent_projects.insert(0, project_path)
        self._recent_projects = self._recent_projects[:20]
        self.recentProjectsChanged.emit(list(self._recent_projects))

    def remove_recent_project(self, path: str | Path) -> None:
        project_path = Path(path).resolve()
        self._recent_projects = [p for p in self._recent_projects if p != project_path]
        self.recentProjectsChanged.emit(list(self._recent_projects))

    def clear_recent_projects(self) -> None:
        self._recent_projects.clear()
        self.recentProjectsChanged.emit([])

    # --------------------------------------------------
    # Create / open / reload
    # --------------------------------------------------

    def create_project(self, path: str | Path, name: str | None = None):
        project = self.manager.create_project(path=path, name=name)
        self._sync_after_open(project.root)
        return project

    def open_project(self, path: str | Path):
        project = self.manager.load_project(Path(path).resolve())
        self._sync_after_open(project.root)

        recovery = self.manager.recovery_path()
        if recovery is not None and recovery.exists():
            self.projectRecoveryAvailable.emit(recovery)
        return project

    def open_recent_project(self, path: str | Path):
        project_path = Path(path).resolve()
        if not project_path.exists():
            self.remove_recent_project(project_path)
            return None
        return self.open_project(project_path)

    def refresh(self):
        if not self.has_project():
            return None
        project = self.manager.reload_current()
        self._apply_project_preferences()
        self._modified = False
        self._last_saved = self.manager.last_saved
        self.projectModified.emit(False)
        return project

    reload = refresh

    def _sync_after_open(self, root: Path) -> None:
        self._apply_project_preferences()
        self._modified = False
        self._last_saved = self.manager.last_saved
        self.add_recent_project(root)
        self.projectOpened.emit(root)
        self.projectModified.emit(False)

    # --------------------------------------------------
    # Save / settings
    # --------------------------------------------------

    def save_project(self) -> bool:
        if not self.has_project():
            return False
        if not self.manager.save_current():
            return False

        self._modified = False
        self._last_saved = self.manager.last_saved
        self.projectModified.emit(False)
        root = self.project_root()
        if root is not None:
            self.projectSaved.emit(root)
        self.manager.clear_recovery()
        return True

    def save_project_as(self, path: str | Path):
        if not self.has_project():
            return None
        project = self.manager.save_as(path)
        self._modified = False
        self._last_saved = self.manager.last_saved
        self.add_recent_project(project.root)
        self.projectModified.emit(False)
        self.projectSaved.emit(project.root)
        return project

    save = save_project
    save_as = save_project_as

    def update_project_settings(self, values: dict, save: bool = True) -> bool:
        project = self.project
        if project is None:
            return False

        project.language = str(values.get("language", project.language))
        project.voice = str(values.get("voice", project.voice))
        project.output_directory = str(
            values.get("output_directory", project.output_directory)
        ) or "output"
        project.auto_save = bool(values.get("auto_save", project.auto_save))

        settings = values.get("settings", {})
        if isinstance(settings, dict):
            project.update_settings(settings)
        else:
            project.touch()

        project.output_path().mkdir(parents=True, exist_ok=True)
        self.manager.mark_modified()
        self._modified = True
        self._apply_project_preferences()
        self.projectModified.emit(True)
        self.projectSettingsChanged.emit(dict(project.settings))

        return self.save_project() if save else True

    # --------------------------------------------------
    # Backups
    # --------------------------------------------------

    def create_backup(self) -> Path | None:
        if not self.has_project():
            return None
        backup = self.manager.create_backup()
        self.projectBackupCreated.emit(backup)
        return backup

    def list_backups(self) -> list[Path]:
        return self.manager.list_backups() if self.has_project() else []

    def restore_backup(self, backup: str | Path) -> bool:
        if not self.has_project():
            return False
        self.manager.create_backup()
        project = self.manager.restore_backup(backup)
        self._apply_project_preferences()
        self._modified = False
        self._last_saved = self.manager.last_saved
        self.add_recent_project(project.root)
        self.projectModified.emit(False)
        self.projectSaved.emit(project.root)
        self.projectBackupRestored.emit(project.root)
        return True

    def delete_backup(self, backup: str | Path) -> bool:
        return self.manager.delete_backup(backup) if self.has_project() else False

    def cleanup_backups(self, keep: int | None = None) -> int:
        if not self.has_project():
            return 0
        if keep is None:
            keep = int(self.project.get_setting("backup_retention", 10))
        return self.manager.cleanup_backups(keep=max(0, int(keep)))

    # --------------------------------------------------
    # Validation / information
    # --------------------------------------------------

    def validate_project(self) -> bool:
        return self.manager.validate_current() if self.has_project() else False

    def statistics(self) -> dict:
        self.sync_modified_state()
        stats = self.manager.statistics()
        stats.update(
            {
                "autosave_enabled": self._autosave_enabled,
                "autosave_interval_ms": self._autosave_interval,
                "recent_projects": len(self._recent_projects),
            }
        )
        return stats

    # --------------------------------------------------
    # Close / shutdown
    # --------------------------------------------------

    def close_project(self, force: bool = False) -> bool:
        if not self.has_project():
            return True
        self.sync_modified_state()
        if self._modified and not force:
            return False
        if not self.manager.close_current(force=force):
            return False

        self._modified = False
        self._last_saved = None
        self.enable_autosave(False)
        self.projectClosed.emit()
        return True

    def save_and_close(self) -> bool:
        if self.has_unsaved_changes() and not self.save_project():
            return False
        return self.close_project(force=True)

    def force_close(self) -> bool:
        return self.close_project(force=True)

    close = close_project

    def reset(self) -> None:
        self._autosave_timer.stop()
        self.manager.reset()
        self._modified = False
        self._last_saved = None

    def dispose(self) -> None:
        self._autosave_timer.stop()
        if self.has_project() and self.has_unsaved_changes():
            try:
                self.manager.autosave()
            except Exception:
                pass
        self.manager.dispose()
        self._modified = False
        self._last_saved = None

    def __del__(self):
        try:
            self.dispose()
        except Exception:
            pass
