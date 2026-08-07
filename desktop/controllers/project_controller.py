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

    Responsibilities:
    - Create projects
    - Open projects
    - Save projects
    - Close projects
    - Notify UI about project state changes

    Milestone 11 additions
    ----------------------
    • Autosave
    • Backup support
    • Recent projects
    • Recovery detection

    Business logic remains inside ProjectManager.
    """

    # --------------------------------------------------
    # Signals
    # --------------------------------------------------

    projectOpened = Signal(Path)

    projectClosed = Signal()

    projectSaved = Signal(Path)

    projectModified = Signal(bool)

    # Milestone 11

    projectAutoSaved = Signal(Path)

    projectBackupCreated = Signal(Path)

    projectRecoveryAvailable = Signal(Path)

    recentProjectsChanged = Signal(list)

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

        self._last_saved: datetime | None = None

        self._autosave_enabled = True

        self._autosave_interval = (
            5 * 60 * 1000
        )  # 5 minutes

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

    @property
    def last_saved(self):

        return self._last_saved

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
    # Internal State
    # --------------------------------------------------

    def mark_modified(
        self,
        value: bool = True,
    ):

        value = bool(value)

        if self._modified == value:

            return

        self._modified = value

        self.projectModified.emit(
            value
        )

    def reset_modified(
        self,
    ):

        self.mark_modified(
            False
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
    ) -> bool:

        if not self._autosave_enabled:

            return False

        if not self.has_project():

            return False

        if not self.modified:

            return False

        try:

            self.manager.save_current()

            self.reset_modified()

            self._last_saved = datetime.now()

            root = self.project_root()

            if root is not None:

                self.projectAutoSaved.emit(
                    root
                )

            return True

        except Exception:

            return False

    # --------------------------------------------------
    # Recent Projects
    # --------------------------------------------------

    def add_recent_project(
        self,
        project: str | Path,
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
        project: str | Path,
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

        root = self.project_root()

        if root is None:

            return None

        return root / ".autosave.project"

    def has_recovery(
        self,
    ) -> bool:

        recovery = self.recovery_file()

        if recovery is None:

            return False

        if recovery.exists():

            self.projectRecoveryAvailable.emit(
                recovery
            )

            return True

        return False

    # --------------------------------------------------
    # Project Creation
    # --------------------------------------------------

    def create_project(
        self,
        path: str | Path,
    ):

        project_path = Path(path)

        if not project_path:

            raise ValueError(
                "Project path is required"
            )

        if (
            project_path.exists()
            and any(project_path.iterdir())
        ):

            raise FileExistsError(
                "Project directory is not empty"
            )

        project = self.manager.create_project(
            project_path
        )

        self.manager.set_current(
            project
        )

        self.reset_modified()

        self._last_saved = datetime.now()

        self.add_recent_project(
            project_path
        )

        self.projectOpened.emit(
            project_path
        )

        return project
    # --------------------------------------------------
    # Project Opening
    # --------------------------------------------------

    def open_project(
        self,
        path: str | Path,
    ):

        project_path = Path(path)

        if not project_path.exists():

            raise FileNotFoundError(
                f"Project not found: {project_path}"
            )

        project = self.manager.load_project(
            project_path
        )

        self.manager.set_current(
            project
        )

        self.reset_modified()

        self._last_saved = datetime.now()

        self.add_recent_project(
            project_path
        )

        self.has_recovery()

        self.projectOpened.emit(
            project_path
        )

        return project

    # --------------------------------------------------
    # Project Reload
    # --------------------------------------------------

    def reload_project(
        self,
    ):

        root = self.project_root()

        if root is None:

            raise RuntimeError(
                "No project is open"
            )

        return self.open_project(
            root
        )

    # --------------------------------------------------
    # Save Project
    # --------------------------------------------------

    def save_project(
        self,
    ):

        if not self.has_project():

            raise RuntimeError(
                "No project is open"
            )

        self.manager.save_current()

        self.reset_modified()

        self._last_saved = datetime.now()

        root = self.project_root()

        if root is not None:

            self.projectSaved.emit(
                root
            )

        return True

    # --------------------------------------------------
    # Save Project As
    # --------------------------------------------------

    def save_project_as(
        self,
        path: str | Path,
    ):

        if not self.has_project():

            raise RuntimeError(
                "No project is open"
            )

        target = Path(path)

        if not target:

            raise ValueError(
                "Target path required"
            )

        self.manager.save_as(
            target
        )

        self.reset_modified()

        self._last_saved = datetime.now()

        self.add_recent_project(
            target
        )

        self.projectSaved.emit(
            target
        )    # --------------------------------------------------
    # Close Project
    # --------------------------------------------------

    def close_project(
        self,
        force: bool = False,
    ):

        if not self.has_project():

            return

        if self.modified and not force:

            raise RuntimeError(
                "Project has unsaved changes"
            )

        self.manager.close_current()

        self.reset_modified()

        self.projectClosed.emit()

    # --------------------------------------------------
    # Unsaved Changes
    # --------------------------------------------------

    def has_unsaved_changes(
        self,
    ) -> bool:

        return self.modified

    def can_close(
        self,
    ) -> bool:

        return not self.modified

    # --------------------------------------------------
    # Project State Helpers
    # --------------------------------------------------

    def current_project(
        self,
    ):

        return self.manager.current

    def project_name(
        self,
    ) -> str | None:

        project = self.current_project()

        if project is None:

            return None

        return getattr(
            project,
            "name",
            None,
        )

    def is_open(
        self,
    ) -> bool:

        return self.manager.current is not None

    # --------------------------------------------------
    # Project Validation
    # --------------------------------------------------

    def validate_project(
        self,
    ) -> bool:

        if not self.is_open():

            return False

        return self.manager.validate_current()

    # --------------------------------------------------
    # Refresh
    # --------------------------------------------------

    def refresh(
        self,
    ):

        if not self.is_open():

            return

        self.manager.refresh()

        if self.has_recovery():

            self.has_recovery()

    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------

    def statistics(
        self,
    ):

        return {

            "project_open":
                self.is_open(),

            "modified":
                self.modified,

            "autosave":
                self._autosave_enabled,

            "recent_projects":
                len(self._recent_projects),

            "last_saved":
                self._last_saved,

        }

    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def dispose(
        self,
    ):

        try:

            self.auto_save()

        except Exception:

            pass

        try:

            self.close_project(
                force=True
            )

        except Exception:

            pass

        try:

            self._autosave_timer.stop()

        except Exception:

            pass

        self.manager = None

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

        return True
