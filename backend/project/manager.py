from __future__ import annotations

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
    • Save project as
    • Close projects
    • Track current project state
    • Create backups
    • Restore backups
    • Autosave/recovery support
    """

    # --------------------------------------------------
    # Configuration
    # --------------------------------------------------

    BACKUP_DIRECTORY_NAME = "backups"

    RECOVERY_DIRECTORY_NAME = ".autosave"

    # --------------------------------------------------
    # Initialization
    # --------------------------------------------------

    def __init__(
        self,
    ):

        self.project: Project | None = None

        self.modified = False

        self.last_saved: datetime | None = None

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

    # --------------------------------------------------
    # Project State
    # --------------------------------------------------

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

    def project_name(
        self,
    ) -> str | None:

        if self.project is None:

            return None

        return self.project.name

    # --------------------------------------------------
    # Set Current Project
    # --------------------------------------------------

    def set_current(
        self,
        project: Project,
    ):

        if not isinstance(
            project,
            Project,
        ):

            raise TypeError(
                "project must be a Project instance"
            )

        self.project = project

        self.modified = False

        self.last_saved = datetime.now()

    # --------------------------------------------------
    # Modification State
    # --------------------------------------------------

    def mark_modified(
        self,
    ):

        self.modified = True

        if self.project is not None:

            self.project.touch()

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
        name: str | None = None,
    ) -> Project:

        project_path = Path(path)

        # ------------------------------------------
        # Validate target path
        # ------------------------------------------

        if project_path.exists():

            if not project_path.is_dir():

                raise ProjectExistsError(
                    f"Project path is not a directory: "
                    f"{project_path}"
                )

            if any(
                project_path.iterdir()
            ):

                raise ProjectExistsError(
                    f"Project directory already exists "
                    f"and is not empty: {project_path}"
                )

        else:

            project_path.mkdir(
                parents=True,
                exist_ok=True,
            )

        # ------------------------------------------
        # Determine project name
        # ------------------------------------------

        project_name = (
            name.strip()
            if name and name.strip()
            else project_path.name
        )

        if not project_name:

            project_name = "Untitled Project"

        # ------------------------------------------
        # Create Project model
        # ------------------------------------------

        project = Project(
            name=project_name,
            root=project_path,
        )

        # ------------------------------------------
        # Initialize project structure
        # ------------------------------------------

        project.initialize()

        # ------------------------------------------
        # Validate project
        # ------------------------------------------

        ProjectValidator.validate_structure(
            project
        )

        # ------------------------------------------
        # Persist project.json
        # ------------------------------------------

        ProjectSerializer.save(
            project
        )

        # ------------------------------------------
        # Make it the current project
        # ------------------------------------------

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

        # ------------------------------------------
        # Validate project directory
        # ------------------------------------------

        if not project_path.exists():

            raise ProjectNotFoundError(
                f"Project not found: "
                f"{project_path}"
            )

        if not project_path.is_dir():

            raise ProjectNotFoundError(
                f"Project path is not a directory: "
                f"{project_path}"
            )

        # ------------------------------------------
        # Verify project.json exists
        # ------------------------------------------

        if not ProjectSerializer.exists(
            project_path
        ):

            raise ProjectNotFoundError(
                f"project.json not found in: "
                f"{project_path}"
            )

        # ------------------------------------------
        # Load using the real serializer API
        # ------------------------------------------

        project = ProjectSerializer.load(
            project_path
        )

        # ------------------------------------------
        # Ensure the loaded project points to the
        # directory that was actually opened.
        # ------------------------------------------

        project.root = project_path

        # ------------------------------------------
        # Validate project structure
        # ------------------------------------------

        ProjectValidator.validate_structure(
            project
        )

        # ------------------------------------------
        # Set as current
        # ------------------------------------------

        self.set_current(
            project
        )

        return project

    # --------------------------------------------------
    # Reload Current Project
    # --------------------------------------------------

    def reload_current(
        self,
    ) -> Project:

        root = self.project_root()

        if root is None:

            raise ProjectNotFoundError(
                "No project is currently open."
            )

        return self.load_project(
            root
        )

    # --------------------------------------------------
    # Project Exists
    # --------------------------------------------------

    def project_exists(
        self,
        path: str | Path,
    ) -> bool:

        project_path = Path(path)

        return (
            project_path.exists()
            and project_path.is_dir()
            and ProjectSerializer.exists(
                project_path
            )
        )
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

        # ------------------------------------------
        # Validate before saving
        # ------------------------------------------

        ProjectValidator.validate_structure(
            project
        )

        # ------------------------------------------
        # Update project timestamp
        # ------------------------------------------

        project.touch()

        # ------------------------------------------
        # Save using the real serializer
        # ------------------------------------------

        ProjectSerializer.save(
            project
        )

        self.project = project

        self.modified = False

        self.last_saved = datetime.now()

        return True

    # --------------------------------------------------
    # Save Current Project
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

        target = Path(
            path
        )

        # ------------------------------------------
        # Validate target
        # ------------------------------------------

        if target.exists():

            if not target.is_dir():

                raise ProjectExistsError(
                    f"Target path is not a directory: "
                    f"{target}"
                )

            # Allow saving into an existing empty
            # directory, but don't silently overwrite
            # an existing project.
            if ProjectSerializer.exists(
                target
            ):

                raise ProjectExistsError(
                    f"A project already exists at: "
                    f"{target}"
                )

        else:

            target.mkdir(
                parents=True,
                exist_ok=True,
            )

        # ------------------------------------------
        # Build a new Project from the existing
        # project's serialized data.
        # ------------------------------------------

        data = self.project.to_dict()

        data["root"] = str(
            target
        )

        data["name"] = target.name

        data["modified"] = (
            datetime.now().isoformat()
        )

        new_project = Project.from_dict(
            data
        )

        # ------------------------------------------
        # Initialize target project
        # ------------------------------------------

        new_project.initialize()

        # ------------------------------------------
        # Validate and save
        # ------------------------------------------

        ProjectValidator.validate_structure(
            new_project
        )

        ProjectSerializer.save(
            new_project
        )

        # ------------------------------------------
        # Make new project current
        # ------------------------------------------

        self.project = new_project

        self.modified = False

        self.last_saved = datetime.now()

        return new_project

    # --------------------------------------------------
    # Create Backup
    # --------------------------------------------------

    def create_backup(
        self,
    ) -> Path:

        if self.project is None:

            raise ProjectNotFoundError(
                "No project is currently open."
            )

        root = self.project_root()

        if root is None:

            raise ProjectNotFoundError(
                "Current project root is unavailable."
            )

        backup_directory = (
            root
            / self.BACKUP_DIRECTORY_NAME
        )

        backup_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        # ------------------------------------------
        # Use the serializer's real backup method.
        # ------------------------------------------

        backup_file = (
            ProjectSerializer.save_backup(
                self.project,
                backup_directory,
            )
        )

        return Path(
            backup_file
        )

    # --------------------------------------------------
    # List Backups
    # --------------------------------------------------

    def list_backups(
        self,
    ) -> list[Path]:

        root = self.project_root()

        if root is None:

            return []

        backup_directory = (
            root
            / self.BACKUP_DIRECTORY_NAME
        )

        if not backup_directory.exists():

            return []

        return sorted(

            [
                file
                for file
                in backup_directory.iterdir()
                if file.is_file()
                and file.suffix.lower() == ".json"
            ],

            key=lambda file:
                file.stat().st_mtime,

            reverse=True,

        )

    # --------------------------------------------------
    # Restore Backup
    # --------------------------------------------------

    def restore_backup(
        self,
        backup_file: str | Path,
    ) -> Project:

        if self.project is None:

            raise ProjectNotFoundError(
                "No project is currently open."
            )

        project_root = self.project_root()

        if project_root is None:

            raise ProjectNotFoundError(
                "Current project root is unavailable."
            )

        backup_path = Path(
            backup_file
        )

        if not backup_path.exists():

            raise ProjectNotFoundError(
                f"Backup file not found: "
                f"{backup_path}"
            )

        # ------------------------------------------
        # Restore using the real serializer API.
        # ------------------------------------------

        restored = (
            ProjectSerializer.restore_backup(
                backup_path,
                project_root,
            )
        )

        # ------------------------------------------
        # Update manager state
        # ------------------------------------------

        self.project = restored

        self.modified = False

        self.last_saved = datetime.now()

        return restored
    # --------------------------------------------------
    # Autosave / Recovery
    # --------------------------------------------------

    def recovery_directory(
        self,
    ) -> Path | None:

        root = self.project_root()

        if root is None:

            return None

        directory = (
            root
            / self.RECOVERY_DIRECTORY_NAME
        )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        return directory

    # --------------------------------------------------

    def recovery_path(
        self,
    ) -> Path | None:

        directory = self.recovery_directory()

        if directory is None:

            return None

        return (
            directory
            / "project.json"
        )

    # --------------------------------------------------

    def autosave(
        self,
    ) -> Path | None:

        if self.project is None:

            return None

        recovery_directory = (
            self.recovery_directory()
        )

        if recovery_directory is None:

            return None

        # ------------------------------------------
        # Save the current project as a recovery
        # snapshot.
        # ------------------------------------------

        recovery_project = Project(
            name=self.project.name,
            root=recovery_directory,
        )

        # Copy the current serialized state.
        data = self.project.to_dict()

        data["name"] = self.project.name

        data["root"] = str(
            recovery_directory
        )

        recovery_project = Project.from_dict(
            data
        )

        recovery_project.root = (
            recovery_directory
        )

        # ------------------------------------------
        # Save using the repository serializer.
        # ------------------------------------------

        ProjectSerializer.save(
            recovery_project
        )

        return (
            recovery_directory
            / "project.json"
        )

    # --------------------------------------------------

    def has_recovery(
        self,
    ) -> bool:

        recovery = self.recovery_path()

        if recovery is None:

            return False

        return (
            recovery.exists()
            and recovery.is_file()
        )

    # --------------------------------------------------

    def load_recovery(
        self,
    ) -> Project:

        recovery = self.recovery_path()

        if recovery is None:

            raise ProjectNotFoundError(
                "Recovery path is unavailable."
            )

        if not recovery.exists():

            raise ProjectNotFoundError(
                "No recovery project is available."
            )

        recovered = ProjectSerializer.load(
            recovery.parent
        )

        return recovered

    # --------------------------------------------------

    def recover(
        self,
    ) -> Project:

        if self.project is None:

            raise ProjectNotFoundError(
                "No project is currently open."
            )

        recovery = self.load_recovery()

        # ------------------------------------------
        # Recovery becomes the active project state.
        # ------------------------------------------

        recovery.root = self.project.root

        recovery.name = self.project.name

        self.project = recovery

        self.modified = True

        return recovery

    # --------------------------------------------------

    def clear_recovery(
        self,
    ) -> bool:

        recovery_directory = (
            self.recovery_directory()
        )

        if recovery_directory is None:

            return False

        if not recovery_directory.exists():

            return False

        try:

            for item in recovery_directory.iterdir():

                if item.is_file():

                    item.unlink()

                elif item.is_dir():

                    import shutil

                    shutil.rmtree(
                        item
                    )

            recovery_directory.rmdir()

            return True

        except Exception:

            return False

    # --------------------------------------------------
    # Backup Cleanup
    # --------------------------------------------------

    def cleanup_backups(
        self,
        keep: int = 10,
    ) -> int:

        keep = max(
            0,
            int(keep),
        )

        backups = self.list_backups()

        removed = 0

        for backup in backups[keep:]:

            try:

                backup.unlink()

                removed += 1

            except Exception:

                continue

        return removed

    # --------------------------------------------------
    # Delete Backup
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

        if not backup_path.is_file():

            return False

        try:

            backup_path.unlink()

            return True

        except Exception:

            return False
    # --------------------------------------------------
    # Validate Current Project
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
    # Can Close
    # --------------------------------------------------

    def can_close(
        self,
    ) -> bool:

        return not self.modified

    # --------------------------------------------------
    # Project State
    # --------------------------------------------------

    def is_open(
        self,
    ) -> bool:

        return self.project is not None

    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        root = self.project_root()

        backup_count = 0

        recovery_available = False

        if root is not None:

            backup_directory = (
                root
                / self.BACKUP_DIRECTORY_NAME
            )

            if backup_directory.exists():

                backup_count = len(
                    [
                        item
                        for item
                        in backup_directory.iterdir()
                        if item.is_file()
                        and item.suffix.lower() == ".json"
                    ]
                )

            recovery_available = (
                self.has_recovery()
            )

        return {

            "has_project":
                self.has_project(),

            "project_name":
                self.project_name(),

            "project_root":
                str(root)
                if root is not None
                else None,

            "modified":
                self.modified,

            "last_saved":
                self.last_saved,

            "backup_count":
                backup_count,

            "recovery_available":
                recovery_available,

        }

    # --------------------------------------------------
    # Shutdown
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
    # Compatibility Helpers
    # --------------------------------------------------

    def save(
        self,
    ) -> bool:

        return self.save_current()

    # --------------------------------------------------

    def open(
        self,
        path: str | Path,
    ) -> Project:

        return self.load_project(
            path
        )

    # --------------------------------------------------

    def close(
        self,
        force: bool = False,
    ) -> bool:

        return self.close_current(
            force=force
        )

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