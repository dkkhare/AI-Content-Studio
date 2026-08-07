from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from backend.project.project import Project
from backend.project.serializer import ProjectSerializer
from backend.project.validator import ProjectValidator


class ProjectManager:
    """
    Central project lifecycle manager.

    Handles:

    - create project
    - open project
    - save project
    - reload project
    - backup
    - recovery
    - project state tracking
    """

    BACKUP_DIRECTORY_NAME = "backups"

    RECOVERY_DIRECTORY_NAME = ".autosave"


    # --------------------------------------------------
    # Initialization
    # --------------------------------------------------

    def __init__(self):

        self.project: Optional[Project] = None

        self.modified: bool = False

        self.last_saved: Optional[datetime] = None


    # --------------------------------------------------
    # Properties
    # --------------------------------------------------

    @property
    def current(self) -> Optional[Project]:

        return self.project


    @property
    def root(self) -> Optional[Path]:

        if self.project is None:

            return None

        return self.project.root


    # --------------------------------------------------
    # Project State
    # --------------------------------------------------

    def has_project(
        self,
    ) -> bool:

        return self.project is not None


    def is_open(
        self,
    ) -> bool:

        return self.has_project()


    def project_root(
        self,
    ) -> Optional[Path]:

        return self.root


    def project_name(
        self,
    ) -> Optional[str]:

        if self.project is None:

            return None

        return self.project.name


    # --------------------------------------------------
    # Modified State
    # --------------------------------------------------

    def mark_modified(
        self,
    ):

        self.modified = True


    def clear_modified(
        self,
    ):

        self.modified = False


    def is_modified(
        self,
    ) -> bool:

        return self.modified


    # --------------------------------------------------
    # Last Saved
    # --------------------------------------------------

    def update_saved_time(
        self,
    ):

        self.last_saved = datetime.now()


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
    # Create Project
    # --------------------------------------------------

    def create_project(
        self,
        path: str | Path,
        name: str | None = None,
    ) -> Project:

        project_path = Path(
            path
        ).resolve()


        if name is None:

            name = project_path.name


        # ------------------------------------------
        # Create project object
        # ------------------------------------------

        project = Project(

            name=name,

            root=project_path,

        )


        # ------------------------------------------
        # Initialize folders/files
        # ------------------------------------------

        project.initialize()


        # ------------------------------------------
        # Validate
        # ------------------------------------------

        ProjectValidator.validate_structure(
            project
        )


        # ------------------------------------------
        # Save initial project.json
        # ------------------------------------------

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

        project_path = Path(
            path
        ).resolve()


        if not project_path.exists():

            raise FileNotFoundError(
                f"Project path does not exist: "
                f"{project_path}"
            )


        # ------------------------------------------
        # Load through serializer
        # ------------------------------------------

        project = ProjectSerializer.load(
            project_path
        )


        # ------------------------------------------
        # Ensure opened path is authoritative
        # ------------------------------------------

        project.root = project_path


        # ------------------------------------------
        # Validate loaded project
        # ------------------------------------------

        ProjectValidator.validate_structure(
            project
        )


        self.set_current(
            project
        )


        return project



    # --------------------------------------------------
    # Open Project Alias
    # --------------------------------------------------

    def open_project(
        self,
        path: str | Path,
    ) -> Project:

        return self.load_project(
            path
        )



    # --------------------------------------------------
    # Reload Current Project
    # --------------------------------------------------

    def reload_current(
        self,
    ) -> Project:

        if self.project is None:

            raise RuntimeError(
                "No project is currently open."
            )


        current_root = self.project.root


        project = ProjectSerializer.load(
            current_root
        )


        project.root = current_root


        ProjectValidator.validate_structure(
            project
        )


        self.set_current(
            project
        )


        return project



    # --------------------------------------------------
    # Save Current Project
    # --------------------------------------------------

    def save_current(
        self,
    ) -> bool:

        if self.project is None:

            raise RuntimeError(
                "No project is currently open."
            )


        ProjectValidator.validate_structure(
            self.project
        )


        self.project.touch()


        ProjectSerializer.save(
            self.project
        )


        self.modified = False


        self.last_saved = datetime.now()


        return True
    # --------------------------------------------------
    # Save As
    # --------------------------------------------------

    def save_as(
        self,
        path: str | Path,
    ) -> Project:

        if self.project is None:

            raise RuntimeError(
                "No project is currently open."
            )


        new_root = Path(
            path
        ).resolve()


        new_root.mkdir(
            parents=True,
            exist_ok=True,
        )


        # ------------------------------------------
        # Update project root
        # ------------------------------------------

        self.project.root = new_root


        ProjectValidator.validate_structure(
            self.project
        )


        ProjectSerializer.save(
            self.project
        )


        self.modified = False


        self.last_saved = datetime.now()


        return self.project



    # --------------------------------------------------
    # Backup Directory
    # --------------------------------------------------

    def backup_directory(
        self,
    ) -> Path:

        if self.project is None:

            raise RuntimeError(
                "No project is currently open."
            )


        directory = (
            self.project.root
            /
            self.BACKUP_DIRECTORY_NAME
        )


        directory.mkdir(
            parents=True,
            exist_ok=True,
        )


        return directory



    # --------------------------------------------------
    # Create Backup
    # --------------------------------------------------

    def create_backup(
        self,
    ) -> Path:

        if self.project is None:

            raise RuntimeError(
                "No project is currently open."
            )


        backup_dir = (
            self.backup_directory()
        )


        backup_file = (
            ProjectSerializer.save_backup(
                self.project,
                backup_dir,
            )
        )


        return backup_file



    # --------------------------------------------------
    # List Backups
    # --------------------------------------------------

    def list_backups(
        self,
    ) -> list[Path]:

        backup_dir = (
            self.backup_directory()
        )


        if not backup_dir.exists():

            return []


        return sorted(

            [

                item

                for item

                in backup_dir.iterdir()

                if (
                    item.is_file()
                    and
                    item.suffix.lower()
                    == ".json"
                )

            ],

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

            raise RuntimeError(
                "No project is currently open."
            )


        backup_path = Path(
            backup_file
        ).resolve()


        project_root = (
            self.project.root
        )


        project = (
            ProjectSerializer.restore_backup(
                backup_path,
                project_root,
            )
        )


        project.root = project_root


        ProjectValidator.validate_structure(
            project
        )


        self.set_current(
            project
        )


        return project



    # --------------------------------------------------
    # Delete Backup
    # --------------------------------------------------

    def delete_backup(
        self,
        backup_file: str | Path,
    ) -> bool:

        backup_path = Path(
            backup_file
        )


        if not backup_path.exists():

            return False


        if not backup_path.is_file():

            return False


        backup_path.unlink()


        return True



    # --------------------------------------------------
    # Cleanup Backups
    # --------------------------------------------------

    def cleanup_backups(
        self,
        keep: int = 10,
    ) -> int:

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
    # Recovery / Autosave
    # --------------------------------------------------

    def recovery_directory(
        self,
    ) -> Path:

        if self.project is None:

            raise RuntimeError(
                "No project is currently open."
            )


        directory = (

            self.project.root

            / self.RECOVERY_DIRECTORY_NAME

        )


        directory.mkdir(
            parents=True,
            exist_ok=True,
        )


        return directory



    # --------------------------------------------------

    def autosave(
        self,
    ) -> Path | None:

        if self.project is None:

            return None


        recovery = (
            self.recovery_directory()
        )


        recovery_file = (
            recovery
            / "project.json"
        )


        data = (
            self.project.to_dict()
        )


        import json


        with open(
            recovery_file,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False,
            )


        return recovery_file



    # --------------------------------------------------

    def has_recovery(
        self,
    ) -> bool:

        if self.project is None:

            return False


        recovery_file = (

            self.project.root

            / self.RECOVERY_DIRECTORY_NAME

            / "project.json"

        )


        return recovery_file.exists()



    # --------------------------------------------------

    def recovery_path(
        self,
    ) -> Path | None:

        if self.project is None:

            return None


        return (

            self.project.root

            / self.RECOVERY_DIRECTORY_NAME

            / "project.json"

        )



    # --------------------------------------------------

    def recover(
        self,
    ) -> Project:

        recovery = self.recovery_path()


        if recovery is None or not recovery.exists():

            raise RuntimeError(
                "No recovery file found."
            )


        import json


        with open(
            recovery,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(
                file
            )


        project = Project.from_dict(
            data
        )


        project.root = (
            self.project.root
        )


        self.set_current(
            project
        )


        self.modified = True


        return project



    # --------------------------------------------------

    def clear_recovery(
        self,
    ) -> bool:

        recovery = self.recovery_path()


        if recovery is None:

            return False


        if recovery.exists():

            recovery.unlink()


            return True


        return False



    # --------------------------------------------------
    # Close / Shutdown
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


        return True



    # --------------------------------------------------

    def shutdown(
        self,
    ):

        try:

            if self.modified:

                self.autosave()


        finally:

            self.close_current(
                force=True
            )



    # --------------------------------------------------
    # Information
    # --------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        return {

            "open":
                self.has_project(),

            "name":
                self.project_name(),

            "root":
                str(
                    self.project_root()
                )
                if self.project_root()
                else None,

            "modified":
                self.modified,

            "has_recovery":
                self.has_recovery(),

            "backups":
                len(
                    self.list_backups()
                )
                if self.has_project()
                else 0,

        }



    # --------------------------------------------------
    # Compatibility Helpers
    # --------------------------------------------------

    def save(
        self,
    ):

        return self.save_current()



    def open(
        self,
        path: str | Path,
    ):

        return self.load_project(
            path
        )



    def close(
        self,
        force: bool = False,
    ):

        return self.close_current(
            force
        )



    def refresh(
        self,
    ):

        return self.reload_current()
    # --------------------------------------------------
    # Project Exists
    # --------------------------------------------------

    def project_exists(
        self,
        path: str | Path,
    ) -> bool:

        project_path = Path(
            path
        )


        return (

            project_path.exists()

            and

            project_path.is_dir()

        )


    # --------------------------------------------------
    # Is Open
    # --------------------------------------------------

    def is_open(
        self,
    ) -> bool:

        return self.project is not None



    # --------------------------------------------------
    # Has Changes Alias
    # --------------------------------------------------

    def has_changes(
        self,
    ) -> bool:

        return self.modified



    # --------------------------------------------------
    # Reload Alias
    # --------------------------------------------------

    def reload(
        self,
    ) -> Project:

        return self.reload_current()



    # --------------------------------------------------
    # Delete Project Recovery Folder
    # --------------------------------------------------

    def remove_recovery_directory(
        self,
    ) -> bool:

        if self.project is None:

            return False


        recovery = (

            self.project.root

            / self.RECOVERY_DIRECTORY_NAME

        )


        if not recovery.exists():

            return False


        import shutil


        shutil.rmtree(
            recovery
        )


        return True



    # --------------------------------------------------
    # Clear Project
    # --------------------------------------------------

    def reset(
        self,
    ):

        self.project = None

        self.modified = False

        self.last_saved = None



    # --------------------------------------------------
    # Dispose
    # --------------------------------------------------

    def dispose(
        self,
    ):

        try:

            if self.project:

                self.close_current(
                    force=True
                )


        finally:

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

            self.dispose()

        except Exception:

            pass