from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import (
    QObject,
    QTimer,
    Signal,
)

from backend.project.manager import ProjectManager


class ProjectController(QObject):
    """
    Desktop controller for project lifecycle management.

    Responsibilities
    ----------------
    • Create projects
    • Open projects
    • Save projects
    • Save projects as
    • Close projects
    • Track modified state
    • Autosave
    • Backup notifications
    • Recovery detection
    • Recent projects

    Business/project persistence logic remains inside
    ProjectManager.
    """

    # --------------------------------------------------
    # Signals
    # --------------------------------------------------

    projectOpened = Signal(Path)

    projectClosed = Signal()

    projectSaved = Signal(Path)

    projectModified = Signal(bool)

    projectAutoSaved = Signal(Path)

    projectBackupCreated = Signal(Path)

    projectRecoveryAvailable = Signal(Path)

    recentProjectsChanged = Signal(list)

    # --------------------------------------------------
    # Initialization
    # --------------------------------------------------

    def __init__(
        self,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.manager = ProjectManager()

        # ------------------------------------------
        # UI/controller state
        # ------------------------------------------

        self._modified = False

        self._recent_projects: list[Path] = []

        self._last_saved: datetime | None = None

        # ------------------------------------------
        # Autosave configuration
        # ------------------------------------------

        self._autosave_enabled = True

        self._autosave_interval = (
            5 * 60 * 1000
        )

        self._autosave_timer = QTimer(
            self
        )

        self._autosave_timer.timeout.connect(
            self.auto_save
        )

        self._autosave_timer.start(
            self._autosave_interval
        )

    # --------------------------------------------------
    # Properties
    # --------------------------------------------------

    @property
    def current(self):

        return self.manager.current

    @property
    def modified(
        self,
    ) -> bool:

        return self._modified

    @property
    def autosave_enabled(
        self,
    ) -> bool:

        return self._autosave_enabled

    @property
    def recent_projects(
        self,
    ) -> list[Path]:

        return list(
            self._recent_projects
        )

    @property
    def last_saved(
        self,
    ) -> datetime | None:

        return self._last_saved

    # --------------------------------------------------
    # Project State
    # --------------------------------------------------

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
    # Modified State
    # --------------------------------------------------

    def mark_modified(
        self,
        value: bool = True,
    ):

        value = bool(
            value
        )

        # ------------------------------------------
        # Keep controller and manager synchronized.
        # ------------------------------------------

        if value:

            self.manager.mark_modified()

        else:

            self.manager.clear_modified()

        if self._modified == value:

            return

        self._modified = value

        self.projectModified.emit(
            value
        )

    # --------------------------------------------------

    def reset_modified(
        self,
    ):

        self.mark_modified(
            False
        )

    # --------------------------------------------------

    def sync_modified_state(
        self,
    ):

        value = bool(
            self.manager.modified
        )

        if self._modified == value:

            return

        self._modified = value

        self.projectModified.emit(
            value
        )

    # --------------------------------------------------
    # Autosave
    # --------------------------------------------------

    def enable_autosave(
        self,
        enabled: bool = True,
    ):

        self._autosave_enabled = bool(
            enabled
        )

        if self._autosave_enabled:

            self._autosave_timer.start(
                self._autosave_interval
            )

        else:

            self._autosave_timer.stop()

    # --------------------------------------------------

    def set_autosave_interval(
        self,
        milliseconds: int,
    ):

        milliseconds = max(
            10000,
            int(milliseconds),
        )

        self._autosave_interval = (
            milliseconds
        )

        if self._autosave_enabled:

            self._autosave_timer.start(
                self._autosave_interval
            )

    # --------------------------------------------------

    def auto_save(
        self,
    ) -> bool:

        if not self._autosave_enabled:

            return False

        if not self.has_project():

            return False

        self.sync_modified_state()

        if not self.modified:

            return False

        try:

            # --------------------------------------
            # IMPORTANT:
            # Autosave creates a recovery snapshot.
            # It must NOT perform a normal save.
            # --------------------------------------

            recovery = self.manager.autosave()

            if recovery is None:

                return False

            root = self.project_root()

            if root is not None:

                self.projectAutoSaved.emit(
                    root
                )

                self.projectRecoveryAvailable.emit(
                    recovery
                )

            return True

        except Exception:

            return False
    # --------------------------------------------------
    # Recent Projects
    # --------------------------------------------------

    def add_recent_project(
        self,
        path: str | Path,
    ):

        project_path = Path(
            path
        ).resolve()

        # Remove existing occurrence.
        self._recent_projects = [

            item

            for item in self._recent_projects

            if item != project_path

        ]

        # Put newest project first.
        self._recent_projects.insert(
            0,
            project_path
        )

        # Keep a reasonable history size.
        self._recent_projects = (
            self._recent_projects[:20]
        )

        self.recentProjectsChanged.emit(
            list(
                self._recent_projects
            )
        )

    # --------------------------------------------------

    def remove_recent_project(
        self,
        path: str | Path,
    ):

        project_path = Path(
            path
        ).resolve()

        self._recent_projects = [

            item

            for item in self._recent_projects

            if item != project_path

        ]

        self.recentProjectsChanged.emit(
            list(
                self._recent_projects
            )
        )

    # --------------------------------------------------

    def clear_recent_projects(
        self,
    ):

        self._recent_projects.clear()

        self.recentProjectsChanged.emit(
            []
        )

    # --------------------------------------------------
    # Recovery
    # --------------------------------------------------

    def has_recovery(
        self,
    ) -> bool:

        if not self.has_project():

            return False

        return self.manager.has_recovery()

    # --------------------------------------------------

    def recovery_path(
        self,
    ) -> Path | None:

        if not self.has_project():

            return None

        return self.manager.recovery_path()

    # --------------------------------------------------

    def load_recovery(
        self,
    ):

        if not self.has_project():

            return None

        return self.manager.load_recovery()

    # --------------------------------------------------

    def recover_project(
        self,
    ) -> bool:

        if not self.has_project():

            return False

        if not self.manager.has_recovery():

            return False

        try:

            project = (
                self.manager.recover()
            )

            self._modified = True

            self.projectModified.emit(
                True
            )

            root = project.root

            self.projectRecoveryAvailable.emit(
                root
            )

            return True

        except Exception:

            return False

    # --------------------------------------------------

    def clear_recovery(
        self,
    ) -> bool:

        try:

            return self.manager.clear_recovery()

        except Exception:

            return False

    # --------------------------------------------------
    # Create Project
    # --------------------------------------------------

    def create_project(
        self,
        path: str | Path,
        name: str | None = None,
    ):

        project = self.manager.create_project(
            path=path,
            name=name,
        )

        # ------------------------------------------
        # Synchronize controller state.
        # ------------------------------------------

        self._modified = False

        self._last_saved = (
            self.manager.last_saved
        )

        self.add_recent_project(
            project.root
        )

        self.projectOpened.emit(
            project.root
        )

        self.projectModified.emit(
            False
        )

        return project

    # --------------------------------------------------
    # Open Project
    # --------------------------------------------------

    def open_project(
        self,
        path: str | Path,
    ):

        project_path = Path(
            path
        ).resolve()

        project = self.manager.load_project(
            project_path
        )

        # ------------------------------------------
        # Synchronize state.
        # ------------------------------------------

        self._modified = False

        self._last_saved = (
            self.manager.last_saved
        )

        self.add_recent_project(
            project.root
        )

        self.projectOpened.emit(
            project.root
        )

        self.projectModified.emit(
            False
        )

        # ------------------------------------------
        # Notify UI if recovery exists.
        # ------------------------------------------

        recovery = (
            self.manager.recovery_path()
        )

        if (
            recovery is not None
            and recovery.exists()
        ):

            self.projectRecoveryAvailable.emit(
                recovery
            )

        return project

    # --------------------------------------------------
    # Open Recent Project
    # --------------------------------------------------

    def open_recent_project(
        self,
        path: str | Path,
    ):

        project_path = Path(
            path
        )

        if not project_path.exists():

            self.remove_recent_project(
                project_path
            )

            return None

        try:

            return self.open_project(
                project_path
            )

        except Exception:

            return None
    # --------------------------------------------------
    # Save Project
    # --------------------------------------------------

    def save_project(
        self,
    ) -> bool:

        if not self.has_project():

            return False

        try:

            result = self.manager.save_current()

            if not result:

                return False

            self._modified = False

            self._last_saved = (
                self.manager.last_saved
            )

            self.projectModified.emit(
                False
            )

            root = self.project_root()

            if root is not None:

                self.projectSaved.emit(
                    root
                )

            # --------------------------------------
            # A successful normal save means the
            # recovery snapshot is no longer needed.
            # --------------------------------------

            try:

                self.manager.clear_recovery()

            except Exception:

                pass

            return True

        except Exception:

            return False

    # --------------------------------------------------
    # Save As
    # --------------------------------------------------

    def save_project_as(
        self,
        path: str | Path,
    ):

        if not self.has_project():

            return None

        try:

            project = self.manager.save_as(
                path
            )

            self._modified = False

            self._last_saved = (
                self.manager.last_saved
            )

            self.projectModified.emit(
                False
            )

            self.add_recent_project(
                project.root
            )

            self.projectSaved.emit(
                project.root
            )

            return project

        except Exception:

            return None

    # --------------------------------------------------
    # Backup
    # --------------------------------------------------

    def create_backup(
        self,
    ) -> Path | None:

        if not self.has_project():

            return None

        try:

            backup = (
                self.manager.create_backup()
            )

            self.projectBackupCreated.emit(
                backup
            )

            return backup

        except Exception:

            return None

    # --------------------------------------------------
    # List Backups
    # --------------------------------------------------

    def list_backups(
        self,
    ) -> list[Path]:

        if not self.has_project():

            return []

        try:

            return self.manager.list_backups()

        except Exception:

            return []

    # --------------------------------------------------
    # Restore Backup
    # --------------------------------------------------

    def restore_backup(
        self,
        backup: str | Path,
    ) -> bool:

        if not self.has_project():

            return False

        try:

            # --------------------------------------
            # Create a safety backup of the current
            # state before restoring another backup.
            # --------------------------------------

            try:

                self.manager.create_backup()

            except Exception:

                pass

            project = (
                self.manager.restore_backup(
                    backup
                )
            )

            self._modified = False

            self._last_saved = (
                self.manager.last_saved
            )

            self.projectModified.emit(
                False
            )

            self.add_recent_project(
                project.root
            )

            self.projectSaved.emit(
                project.root
            )

            return True

        except Exception:

            return False

    # --------------------------------------------------
    # Delete Backup
    # --------------------------------------------------

    def delete_backup(
        self,
        backup: str | Path,
    ) -> bool:

        try:

            return self.manager.delete_backup(
                backup
            )

        except Exception:

            return False

    # --------------------------------------------------
    # Cleanup Backups
    # --------------------------------------------------

    def cleanup_backups(
        self,
        keep: int = 10,
    ) -> int:

        if not self.has_project():

            return 0

        try:

            return self.manager.cleanup_backups(
                keep=keep
            )

        except Exception:

            return 0

    # --------------------------------------------------
    # Refresh Project
    # --------------------------------------------------

    def refresh(
        self,
    ):

        if not self.has_project():

            return None

        try:

            project = (
                self.manager.reload_current()
            )

            self._modified = False

            self._last_saved = (
                self.manager.last_saved
            )

            self.projectModified.emit(
                False
            )

            return project

        except Exception:

            return None
    # --------------------------------------------------
    # Close Project
    # --------------------------------------------------

    def close_project(
        self,
        force: bool = False,
    ) -> bool:

        if not self.has_project():

            return True

        # ------------------------------------------
        # Synchronize state before checking whether
        # there are unsaved changes.
        # ------------------------------------------

        self.sync_modified_state()

        if self.modified and not force:

            raise RuntimeError(
                "Project has unsaved changes."
            )

        try:

            result = self.manager.close_current(
                force=force
            )

            if not result:

                return False

            self._modified = False

            self._last_saved = None

            self.projectClosed.emit()

            return True

        except Exception:

            return False

    # --------------------------------------------------
    # Unsaved Changes
    # --------------------------------------------------

    def has_unsaved_changes(
        self,
    ) -> bool:

        self.sync_modified_state()

        return self.modified

    # --------------------------------------------------

    def can_close(
        self,
    ) -> bool:

        return not self.has_unsaved_changes()

    # --------------------------------------------------
    # Save Before Close
    # --------------------------------------------------

    def save_and_close(
        self,
    ) -> bool:

        if not self.has_project():

            return True

        if self.has_unsaved_changes():

            if not self.save_project():

                return False

        return self.close_project(
            force=True
        )

    # --------------------------------------------------
    # Force Close
    # --------------------------------------------------

    def force_close(
        self,
    ) -> bool:

        return self.close_project(
            force=True
        )

    # --------------------------------------------------
    # Current Project
    # --------------------------------------------------

    def current_project(
        self,
    ):

        return self.manager.current

    # --------------------------------------------------

    def project_name(
        self,
    ) -> str | None:

        return self.manager.project_name()

    # --------------------------------------------------

    def is_open(
        self,
    ) -> bool:

        return self.manager.is_open()

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------

    def validate_project(
        self,
    ) -> bool:

        if not self.has_project():

            return False

        try:

            return self.manager.validate_current()

        except Exception:

            return False

    # --------------------------------------------------
    # Synchronize Manager State
    # --------------------------------------------------

    def synchronize(
        self,
    ):

        if not self.has_project():

            self._modified = False

            self._last_saved = None

            return

        self.sync_modified_state()

        self._last_saved = (
            self.manager.last_saved
        )

    # --------------------------------------------------
    # Project Statistics
    # --------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        self.synchronize()

        try:

            manager_statistics = (
                self.manager.statistics()
            )

        except Exception:

            manager_statistics = {}

        return {

            "project_open":
                self.has_project(),

            "project_name":
                self.project_name(),

            "project_root":
                str(
                    self.project_root()
                )
                if self.project_root()
                is not None
                else None,

            "modified":
                self.modified,

            "autosave":
                self.autosave_enabled,

            "last_saved":
                self.last_saved,

            "recent_projects":
                len(
                    self._recent_projects
                ),

            "manager":
                manager_statistics,

        }

    # --------------------------------------------------
    # Clear Current Project
    # --------------------------------------------------

    def reset(
        self,
    ):

        try:

            self._autosave_timer.stop()

        except Exception:

            pass

        try:

            self.manager.reset()

        except Exception:

            pass

        self._modified = False

        self._last_saved = None

    # --------------------------------------------------
    # Dispose
    # --------------------------------------------------

    def dispose(
        self,
    ):

        # ------------------------------------------
        # Stop autosave first.
        # ------------------------------------------

        try:

            self._autosave_timer.stop()

        except Exception:

            pass

        # ------------------------------------------
        # Give the current project a final autosave
        # snapshot if necessary.
        # ------------------------------------------

        try:

            self.sync_modified_state()

            if self.modified:

                self.manager.autosave()

        except Exception:

            pass

        # ------------------------------------------
        # Close manager state without forcing a
        # normal save.
        # ------------------------------------------

        try:

            self.manager.close_current(
                force=True
            )

        except Exception:

            pass

        self._modified = False

        self._last_saved = None

    # --------------------------------------------------
    # Destructor
    # --------------------------------------------------

    def __del__(
        self,
    ):

        try:

            self.dispose()

        except Exception:

            pass