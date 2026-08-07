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
    Connects the desktop UI layer with the backend
    ProjectManager.

    Milestone 11 additions
    ----------------------
    • Autosave support
    • Backup notifications
    • Recent project history
    • Recovery support
    • Dirty-state tracking
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

    recentProjectsChanged = Signal(list)

    recoveryAvailable = Signal(Path)

    # --------------------------------------------------

    def __init__(
        self,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.manager = ProjectManager()

        self._modified = False

        # ------------------------------------------
        # Milestone 11 State
        # ------------------------------------------

        self._recent_projects: list[Path] = []

        self._last_saved = None

        self._autosave_enabled = True

        self._autosave_interval = 5 * 60 * 1000

        self._autosave_timer = QTimer(self)

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
    def modified(self):

        return self._modified

    @property
    def autosave_enabled(self):

        return self._autosave_enabled

    @property
    def recent_projects(self):

        return list(
            self._recent_projects
        )
    # --------------------------------------------------
    # Project Information
    # --------------------------------------------------

    def has_project(
        self,
    ) -> bool:

        return self.current is not None

    def project_root(
        self,
    ) -> Path | None:

        project = self.current

        if project is None:

            return None

        return Path(project.root)

    def project_file(
        self,
    ) -> Path | None:

        project = self.current

        if project is None:

            return None

        filename = getattr(

            project,

            "project_file",

            None,

        )

        if filename:

            return Path(filename)

        return None

    # --------------------------------------------------
    # Modified State
    # --------------------------------------------------

    def set_modified(
        self,
        modified: bool = True,
    ):

        modified = bool(modified)

        if self._modified == modified:

            return

        self._modified = modified

        self.projectModified.emit(
            modified
        )

    def clear_modified(
        self,
    ):

        self.set_modified(
            False
        )

    def touch(
        self,
    ):

        self.set_modified(
            True
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

    def set_autosave_interval(
        self,
        milliseconds: int,
    ):

        milliseconds = max(
            10000,
            int(milliseconds),
        )

        self._autosave_interval = milliseconds

        if self._autosave_enabled:

            self._autosave_timer.start(
                milliseconds
            )

    def auto_save(
        self,
    ):

        if not self._autosave_enabled:

            return

        if not self.has_project():

            return

        if not self.modified:

            return

        try:

            project = self.current

            self.manager.save(project)

            self._last_saved = datetime.now()

            self.clear_modified()

            project_file = self.project_file()

            if project_file is not None:

                self.projectAutoSaved.emit(
                    project_file
                )

        except Exception:

            # Autosave must never interrupt the UI.
            pass
    # --------------------------------------------------
    # Recent Projects
    # --------------------------------------------------

    def add_recent_project(
        self,
        project: Path | str,
    ):

        project = Path(project)

        if project in self._recent_projects:

            self._recent_projects.remove(
                project
            )

        self._recent_projects.insert(
            0,
            project,
        )

        self._recent_projects = (

            self._recent_projects[:10]

        )

        self.recentProjectsChanged.emit(

            list(self._recent_projects)

        )

    def remove_recent_project(
        self,
        project: Path | str,
    ):

        project = Path(project)

        if project in self._recent_projects:

            self._recent_projects.remove(
                project
            )

            self.recentProjectsChanged.emit(

                list(self._recent_projects)

            )

    def clear_recent_projects(
        self,
    ):

        self._recent_projects.clear()

        self.recentProjectsChanged.emit([])

    # --------------------------------------------------
    # Recovery
    # --------------------------------------------------

    def recovery_file(
        self,
    ) -> Path | None:

        project = self.project_root()

        if project is None:

            return None

        return project / ".autosave.project"

    def has_recovery(
        self,
    ) -> bool:

        recovery = self.recovery_file()

        if recovery is None:

            return False

        exists = recovery.exists()

        if exists:

            self.recoveryAvailable.emit(
                recovery
            )

        return exists

    # --------------------------------------------------
    # Backup
    # --------------------------------------------------

    def create_backup(
        self,
    ) -> Path | None:

        project = self.project_root()

        if project is None:

            return None

        backup_dir = project / "backups"

        backup_dir.mkdir(

            parents=True,

            exist_ok=True,

        )

        filename = datetime.now().strftime(

            "%Y%m%d_%H%M%S.project"

        )

        backup = backup_dir / filename

        try:

            self.manager.save_as(

                self.current,

                backup,

            )

        except Exception:

            return None

        self.projectBackupCreated.emit(
            backup
        )

        return backup
    # --------------------------------------------------
    # Recent Projects
    # --------------------------------------------------

    def add_recent_project(
        self,
        project: Path | str,
    ):

        project = Path(project)

        if project in self._recent_projects:

            self._recent_projects.remove(
                project
            )

        self._recent_projects.insert(
            0,
            project,
        )

        self._recent_projects = (

            self._recent_projects[:10]

        )

        self.recentProjectsChanged.emit(

            list(self._recent_projects)

        )

    def remove_recent_project(
        self,
        project: Path | str,
    ):

        project = Path(project)

        if project in self._recent_projects:

            self._recent_projects.remove(
                project
            )

            self.recentProjectsChanged.emit(

                list(self._recent_projects)

            )

    def clear_recent_projects(
        self,
    ):

        self._recent_projects.clear()

        self.recentProjectsChanged.emit([])

    # --------------------------------------------------
    # Recovery
    # --------------------------------------------------

    def recovery_file(
        self,
    ) -> Path | None:

        project = self.project_root()

        if project is None:

            return None

        return project / ".autosave.project"

    def has_recovery(
        self,
    ) -> bool:

        recovery = self.recovery_file()

        if recovery is None:

            return False

        exists = recovery.exists()

        if exists:

            self.recoveryAvailable.emit(
                recovery
            )

        return exists

    # --------------------------------------------------
    # Backup
    # --------------------------------------------------

    def create_backup(
        self,
    ) -> Path | None:

        project = self.project_root()

        if project is None:

            return None

        backup_dir = project / "backups"

        backup_dir.mkdir(

            parents=True,

            exist_ok=True,

        )

        filename = datetime.now().strftime(

            "%Y%m%d_%H%M%S.project"

        )

        backup = backup_dir / filename

        try:

            self.manager.save_as(

                self.current,

                backup,

            )

        except Exception:

            return None

        self.projectBackupCreated.emit(
            backup
        )
    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------

    def statistics(
        self,
    ):

        return {

            "has_project": self.has_project(),

            "modified": self.modified,

            "autosave_enabled": self._autosave_enabled,

            "recent_projects": len(
                self._recent_projects
            ),

            "last_saved": self._last_saved,

        }

    # --------------------------------------------------
    # Project Summary
    # --------------------------------------------------

    def project_summary(
        self,
    ):

        if not self.has_project():

            return {}

        project = self.current

        return {

            "name": getattr(
                project,
                "name",
                "",
            ),

            "root": str(
                self.project_root()
            )
            if self.project_root()
            else "",

            "modified": self.modified,

            "last_saved": self._last_saved,

        }

    # --------------------------------------------------
    # Debug
    # --------------------------------------------------

    def debug_info(
        self,
    ):

        return {

            "controller": self.__class__.__name__,

            "project_loaded": self.has_project(),

            "modified": self.modified,

            "autosave": self._autosave_enabled,

            "autosave_interval":
                self._autosave_interval,

            "recent_projects":
                len(self._recent_projects),

        }

    # --------------------------------------------------
    # Reset
    # --------------------------------------------------

    def reset(
        self,
    ):

        self._modified = False

        self._last_saved = None

        self._recent_projects.clear()

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
        return backup
