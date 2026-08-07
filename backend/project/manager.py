from __future__ import annotations

import shutil

from datetime import datetime

from pathlib import Path


from backend.project.exceptions import (

    ProjectExistsError,

    ProjectNotFoundError,

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
    Central backend service for project lifecycle.

    Responsibilities
    ----------------
    • Create projects
    • Open projects
    • Save projects
    • Close projects
    • Track current project state
    • Create backups
    • Recovery support

    UI logic must not exist here.
    """

    def __init__(
        self,
    ):

        self.project: Project | None = None

        self.modified = False

        self.last_saved: datetime | None = None

        self.backup_directory_name = "backups"

        self.recovery_filename = ".autosave.project"

    # --------------------------------------------------
    # Properties
    # --------------------------------------------------

    @property
    def current(
        self,
    ) -> Project | None:

        return self.project

    @property
    def has_current(
        self,
    ) -> bool:

        return self.project is not None

    def has_project(
        self,
    ) -> bool:

        return self.project is not None

    def project_root(
        self,
    ) -> Path | None:

        if self.project is None:

            return None

        return self.project.root

    # --------------------------------------------------
    # State Management
    # --------------------------------------------------

    def set_current(
        self,
        project: Project,
    ):

        self.project = project

        self.modified = False

        self.last_saved = datetime.now()

    def mark_modified(
        self,
    ):

        self.modified = True

    def clear_modified(
        self,
    ):

        self.modified = False

    def has_changes(
        self,
    ) -> bool:

        return self.modified
    # --------------------------------------------------
    # Create Project
    # --------------------------------------------------

    def create_project(
        self,
        path: str | Path,
    ) -> Project:

        project_path = Path(path)

        if project_path.exists():

            if any(
                project_path.iterdir()
            ):

                raise ProjectExistsError(
                    "Project directory already exists "
                    "and is not empty"
                )

        else:

            project_path.mkdir(
                parents=True,
                exist_ok=True,
            )

        project = Project(
            root=project_path
        )

        ProjectValidator.validate_structure(
            project
        )

        ProjectSerializer.save(
            project
        )

        self.set_current(
            project
        )

        return project

    # --------------------------------------------------
    # Load Project
    # --------------------------------------------------

    def load_project(
        self,
        path: str | Path,
    ) -> Project:

        project_path = Path(path)

        if not project_path.exists():

            raise ProjectNotFoundError(
                f"Project not found: "
                f"{project_path}"
            )

        project = (
            ProjectSerializer.load(
                project_path
            )
        )

        ProjectValidator.validate_structure(
            project
        )

        self.set_current(
            project
        )

        return project

    # --------------------------------------------------
    # Recovery Detection
    # --------------------------------------------------

    def recovery_path(
        self,
        path: str | Path | None = None,
    ) -> Path | None:

        if path is None:

            root = self.project_root()

        else:

            root = Path(path)

        if root is None:

            return None

        return (
            Path(root)
            / self.recovery_filename
        )

    def has_recovery(
        self,
        path: str | Path | None = None,
    ) -> bool:

        recovery = self.recovery_path(
            path
        )

        if recovery is None:

            return False

        return recovery.exists()

    # --------------------------------------------------
    # Backup Directory
    # --------------------------------------------------

    def backup_directory(
        self,
        path: str | Path | None = None,
    ) -> Path | None:

        if path is None:

            root = self.project_root()

        else:

            root = Path(path)

        if root is None:

            return None

        directory = (
            Path(root)
            / self.backup_directory_name
        )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        return directory
    # --------------------------------------------------
    # Save Project
    # --------------------------------------------------

    def save_project(
        self,
        project: Project | None = None,
    ) -> bool:

        if project is None:

            project = self.project

        if project is None:

            raise ProjectNotFoundError(
                "No project is currently open."
            )

        ProjectValidator.validate_structure(
            project
        )

        ProjectSerializer.save(
            project
        )

        self.project = project

        self.modified = False

        self.last_saved = datetime.now()

        return True

    # --------------------------------------------------
    # Save Current
    # --------------------------------------------------

    def save_current(
        self,
    ) -> bool:

        if self.project is None:

            raise ProjectNotFoundError(
                "No project is currently open."
            )

        return self.save_project(
            self.project
        )

    # --------------------------------------------------
    # Save As
    # --------------------------------------------------

    def save_as(
        self,
        path: str | Path,
    ) -> Project:

        if self.project is None:

            raise ProjectNotFoundError(
                "No project is currently open."
            )

        target = Path(path)

        target.mkdir(
            parents=True,
            exist_ok=True,
        )

        # ------------------------------------------
        # Create a new project object at the target
        # ------------------------------------------

        new_project = Project(
            root=target
        )

        # ------------------------------------------
        # Copy project data through serializer
        # ------------------------------------------

        new_project.metadata = (
            dict(
                getattr(
                    self.project,
                    "metadata",
                    {},
                )
            )
        )

        ProjectValidator.validate_structure(
            new_project
        )

        ProjectSerializer.save(
            new_project
        )

        self.project = new_project

        self.modified = False

        self.last_saved = datetime.now()

        return new_project

    # --------------------------------------------------
    # Autosave
    # --------------------------------------------------

    def autosave(
        self,
    ) -> Path | None:

        if self.project is None:

            return None

        if not self.modified:

            return None

        recovery = self.recovery_path()

        if recovery is None:

            return None

        recovery.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # ------------------------------------------
        # Save recovery copy without changing the
        # current project's normal saved state.
        # ------------------------------------------

        recovery_project = Project(
            root=recovery
        )

        recovery_project.metadata = (
            dict(
                getattr(
                    self.project,
                    "metadata",
                    {},
                )
            )
        )

        ProjectSerializer.save(
            recovery_project
        )

        return recovery

    # --------------------------------------------------
    # Create Backup
    # --------------------------------------------------

    def create_backup(
        self,
    ) -> Path | None:

        if self.project is None:

            return None

        source = self.project_root()

        if source is None:

            return None

        backup_root = self.backup_directory()

        if backup_root is None:

            return None

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        backup_path = (
            backup_root
            / f"backup_{timestamp}"
        )

        shutil.copytree(
            source,
            backup_path,
            ignore=shutil.ignore_patterns(
                self.backup_directory_name,
                self.recovery_filename,
            ),
        )

        return backup_path
    # --------------------------------------------------
    # Recover Project
    # --------------------------------------------------

    def recover(
        self,
        path: str | Path | None = None,
    ) -> Project:

        recovery = self.recovery_path(
            path
        )

        if recovery is None:

            raise ProjectNotFoundError(
                "Recovery path is not available."
            )

        if not recovery.exists():

            raise ProjectNotFoundError(
                f"Recovery project not found: "
                f"{recovery}"
            )

        # ------------------------------------------
        # Determine the original project directory
        # ------------------------------------------

        if path is None:

            original_root = self.project_root()

        else:

            original_root = Path(path)

        if original_root is None:

            raise ProjectNotFoundError(
                "Original project path is not available."
            )

        # ------------------------------------------
        # If the recovery directory is already the
        # project root, simply load it.
        # ------------------------------------------

        if recovery.resolve() == original_root.resolve():

            return self.load_project(
                recovery
            )

        # ------------------------------------------
        # Load the recovery project.
        #
        # We intentionally use the existing serializer
        # through load_project() rather than assuming a
        # new serializer API.
        # ------------------------------------------

        recovered_project = (
            ProjectSerializer.load(
                recovery
            )
        )

        ProjectValidator.validate_structure(
            recovered_project
        )

        # ------------------------------------------
        # Replace the current project with the
        # recovered project.
        # ------------------------------------------

        self.set_current(
            recovered_project
        )

        self.modified = True

        return recovered_project

    # --------------------------------------------------
    # Delete Recovery
    # --------------------------------------------------

    def clear_recovery(
        self,
        path: str | Path | None = None,
    ) -> bool:

        recovery = self.recovery_path(
            path
        )

        if recovery is None:

            return False

        if not recovery.exists():

            return False

        try:

            if recovery.is_dir():

                shutil.rmtree(
                    recovery
                )

            else:

                recovery.unlink()

            return True

        except Exception:

            return False

    # --------------------------------------------------
    # Backup Management
    # --------------------------------------------------

    def list_backups(
        self,
    ) -> list[Path]:

        directory = self.backup_directory()

        if directory is None:

            return []

        if not directory.exists():

            return []

        return sorted(

            [
                item
                for item in directory.iterdir()
                if item.is_dir()
            ],

            key=lambda item: item.stat().st_mtime,

            reverse=True,

        )

    # --------------------------------------------------
    # Restore Backup
    # --------------------------------------------------

    def restore_backup(
        self,
        backup: str | Path,
    ) -> Project:

        if self.project is None:

            raise ProjectNotFoundError(
                "No project is currently open."
            )

        backup_path = Path(
            backup
        )

        if not backup_path.exists():

            raise ProjectNotFoundError(
                f"Backup not found: "
                f"{backup_path}"
            )

        if not backup_path.is_dir():

            raise ValueError(
                "Backup path must be a directory."
            )

        # ------------------------------------------
        # Create a safety backup before restoring.
        # ------------------------------------------

        self.create_backup()

        # ------------------------------------------
        # Restore backup contents into the current
        # project directory.
        # ------------------------------------------

        project_root = self.project_root()

        if project_root is None:

            raise ProjectNotFoundError(
                "Current project root is unavailable."
            )

        for item in backup_path.iterdir():

            destination = (
                project_root
                / item.name
            )

            if item.is_dir():

                shutil.copytree(
                    item,
                    destination,
                    dirs_exist_ok=True,
                )

            else:

                shutil.copy2(
                    item,
                    destination,
                )

        # ------------------------------------------
        # Reload through the existing serializer.
        # ------------------------------------------

        restored = self.load_project(
            project_root
        )

        self.modified = False

        self.last_saved = datetime.now()

        return restored

    # --------------------------------------------------
    # Project Validation
    # --------------------------------------------------

    def validate_current(
        self,
    ) -> bool:

        if self.project is None:

            return False

        try:

            ProjectValidator.validate_structure(
                self.project
            )

            return True

        except Exception:

            return False
    # --------------------------------------------------
    # Close Current Project
    # --------------------------------------------------

    def close_current(
        self,
        force: bool = False,
    ) -> bool:

        if self.project is None:

            return True

        if self.modified and not force:

            raise RuntimeError(
                "Project has unsaved changes."
            )

        self.project = None

        self.modified = False

        self.last_saved = None

        return True

    # --------------------------------------------------
    # Backup Cleanup
    # --------------------------------------------------

    def delete_backup(
        self,
        backup: str | Path,
    ) -> bool:

        backup_path = Path(
            backup
        )

        if not backup_path.exists():

            return False

        try:

            if backup_path.is_dir():

                shutil.rmtree(
                    backup_path
                )

            else:

                backup_path.unlink()

            return True

        except Exception:

            return False

    # --------------------------------------------------
    # Keep Recent Backups
    # --------------------------------------------------

    def cleanup_backups(
        self,
        keep: int = 10,
    ) -> int:

        backups = self.list_backups()

        keep = max(
            0,
            int(keep),
        )

        removed = 0

        for backup in backups[keep:]:

            if self.delete_backup(
                backup
            ):

                removed += 1

        return removed

    # --------------------------------------------------
    # Project Statistics
    # --------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        root = self.project_root()

        backup_count = 0

        recovery_exists = False

        if root is not None:

            backups = self.backup_directory()

            if backups is not None:

                if backups.exists():

                    backup_count = len(
                        [
                            item
                            for item in backups.iterdir()
                            if item.is_dir()
                        ]
                    )

            recovery_exists = (
                self.has_recovery()
            )

        return {

            "has_project":
                self.has_project(),

            "modified":
                self.modified,

            "last_saved":
                self.last_saved,

            "project_root":
                str(root)
                if root is not None
                else "",

            "backup_count":
                backup_count,

            "recovery_available":
                recovery_exists,

        }

    # --------------------------------------------------
    # Safe Shutdown
    # --------------------------------------------------

    def shutdown(
        self,
        save: bool = True,
    ) -> bool:

        if self.project is None:

            return True

        try:

            if save and self.modified:

                self.save_current()

            self.close_current(
                force=True
            )

            return True

        except Exception:

            return False

    # --------------------------------------------------
    # Reset
    # --------------------------------------------------

    def reset(
        self,
    ):

        self.project = None

        self.modified = False

        self.last_saved = None

    # --------------------------------------------------
    # Destructor
    # --------------------------------------------------

    def __del__(
        self,
    ):

        try:

            self.reset()

        except Exception:

            pass