from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from backend.project.project import Project
from backend.project.serializer import ProjectSerializer
from backend.project.validator import ProjectValidator


class ProjectManager:
    """
    Central project lifecycle manager.

    Handles project creation, loading, saving, reloading,
    backups, autosave/recovery, validation, and state tracking.
    """

    BACKUP_DIRECTORY_NAME = "backups"
    RECOVERY_DIRECTORY_NAME = ".autosave"

    def __init__(self):
        self.project: Optional[Project] = None
        self.modified: bool = False
        self.last_saved: Optional[datetime] = None

    @property
    def current(self) -> Optional[Project]:
        return self.project

    @property
    def root(self) -> Optional[Path]:
        return self.project.root if self.project is not None else None

    def has_project(self) -> bool:
        return self.project is not None

    def is_open(self) -> bool:
        return self.has_project()

    def project_root(self) -> Optional[Path]:
        return self.root

    def project_name(self) -> Optional[str]:
        return self.project.name if self.project is not None else None

    def mark_modified(self) -> None:
        self.modified = True

    def clear_modified(self) -> None:
        self.modified = False

    def is_modified(self) -> bool:
        return self.modified

    def has_changes(self) -> bool:
        return self.modified

    def update_saved_time(self) -> None:
        self.last_saved = datetime.now()

    def set_current(self, project: Project) -> Project:
        if not isinstance(project, Project):
            raise TypeError("project must be a Project instance")

        self.project = project
        self.modified = False
        self.update_saved_time()
        return project

    def reset(self) -> None:
        self.project = None
        self.modified = False
        self.last_saved = None

    def create_project(
        self,
        path: str | Path,
        name: str | None = None,
    ) -> Project:
        project_path = Path(path).resolve()
        project_name = (name or project_path.name).strip()

        if not project_name:
            raise ValueError("Project name is required.")

        project = Project(
            name=project_name,
            root=project_path,
        )
        project.initialize()
        ProjectValidator.validate_structure(project)
        ProjectSerializer.save(project)
        return self.set_current(project)

    def load_project(self, path: str | Path) -> Project:
        project_path = Path(path).resolve()

        if not project_path.exists() or not project_path.is_dir():
            raise FileNotFoundError(
                f"Project path does not exist: {project_path}"
            )

        if not ProjectSerializer.exists(project_path):
            raise FileNotFoundError(
                f"project.json not found in: {project_path}"
            )

        project = ProjectSerializer.load(project_path)
        project.root = project_path
        ProjectValidator.validate_structure(project)
        return self.set_current(project)

    def open_project(self, path: str | Path) -> Project:
        return self.load_project(path)

    def reload_current(self) -> Project:
        if self.project is None:
            raise RuntimeError("No project is currently open.")

        current_root = self.project.root
        project = ProjectSerializer.load(current_root)
        project.root = current_root
        ProjectValidator.validate_structure(project)
        return self.set_current(project)

    def refresh(self) -> Project:
        return self.reload_current()

    def reload(self) -> Project:
        return self.reload_current()

    def save_current(self) -> bool:
        if self.project is None:
            raise RuntimeError("No project is currently open.")

        ProjectValidator.validate_structure(self.project)
        self.project.touch()
        ProjectSerializer.save(self.project)
        self.clear_modified()
        self.update_saved_time()
        return True

    def save(self) -> bool:
        return self.save_current()

    def save_as(self, path: str | Path) -> Project:
        if self.project is None:
            raise RuntimeError("No project is currently open.")

        new_root = Path(path).resolve()
        old_root = self.project.root

        self.project.root = new_root
        try:
            self.project.initialize()
            ProjectValidator.validate_structure(self.project)
            ProjectSerializer.save(self.project)
        except Exception:
            self.project.root = old_root
            raise

        self.clear_modified()
        self.update_saved_time()
        return self.project

    def backup_directory(self) -> Path:
        if self.project is None:
            raise RuntimeError("No project is currently open.")

        directory = self.project.root / self.BACKUP_DIRECTORY_NAME
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def create_backup(self) -> Path:
        if self.project is None:
            raise RuntimeError("No project is currently open.")

        return ProjectSerializer.save_backup(
            self.project,
            self.backup_directory(),
        )

    def list_backups(self) -> list[Path]:
        if self.project is None:
            return []

        directory = self.project.root / self.BACKUP_DIRECTORY_NAME
        if not directory.exists():
            return []

        return sorted(
            (
                item
                for item in directory.iterdir()
                if item.is_file() and item.suffix.lower() == ".json"
            ),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )

    def restore_backup(self, backup_file: str | Path) -> Project:
        if self.project is None:
            raise RuntimeError("No project is currently open.")

        backup_path = Path(backup_file).resolve()
        project_root = self.project.root
        project = ProjectSerializer.restore_backup(
            backup_path,
            project_root,
        )
        project.root = project_root
        ProjectValidator.validate_structure(project)
        return self.set_current(project)

    def delete_backup(self, backup_file: str | Path) -> bool:
        backup_path = Path(backup_file)

        if not backup_path.exists() or not backup_path.is_file():
            return False

        backup_path.unlink()
        return True

    def cleanup_backups(self, keep: int = 10) -> int:
        keep = max(0, int(keep))
        backups = self.list_backups()
        removed = 0

        for backup in backups[keep:]:
            try:
                backup.unlink()
                removed += 1
            except OSError:
                continue

        return removed

    def recovery_directory(self) -> Path:
        if self.project is None:
            raise RuntimeError("No project is currently open.")

        directory = self.project.root / self.RECOVERY_DIRECTORY_NAME
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def recovery_path(self) -> Optional[Path]:
        if self.project is None:
            return None

        return (
            self.project.root
            / self.RECOVERY_DIRECTORY_NAME
            / ProjectSerializer.PROJECT_FILE
        )

    def autosave(self) -> Optional[Path]:
        if self.project is None:
            return None

        recovery_file = (
            self.recovery_directory()
            / ProjectSerializer.PROJECT_FILE
        )
        temp_file = recovery_file.with_suffix(".tmp")

        with open(temp_file, "w", encoding="utf-8") as file:
            json.dump(
                self.project.to_dict(),
                file,
                indent=4,
                ensure_ascii=False,
            )

        temp_file.replace(recovery_file)
        return recovery_file

    def has_recovery(self) -> bool:
        recovery = self.recovery_path()
        return bool(recovery and recovery.is_file())

    def load_recovery(self) -> Project:
        if self.project is None:
            raise RuntimeError("No project is currently open.")

        recovery = self.recovery_path()
        if recovery is None or not recovery.exists():
            raise RuntimeError("No recovery file found.")

        with open(recovery, "r", encoding="utf-8") as file:
            data = json.load(file)

        project = Project.from_dict(data)
        project.root = self.project.root
        ProjectValidator.validate_structure(project)
        return project

    def recover(self) -> Project:
        project = self.load_recovery()
        self.project = project
        self.modified = True
        return project

    def clear_recovery(self) -> bool:
        recovery = self.recovery_path()
        if recovery is None or not recovery.exists():
            return False

        recovery.unlink()

        directory = recovery.parent
        try:
            directory.rmdir()
        except OSError:
            pass

        return True

    def remove_recovery_directory(self) -> bool:
        if self.project is None:
            return False

        directory = self.project.root / self.RECOVERY_DIRECTORY_NAME
        if not directory.exists():
            return False

        shutil.rmtree(directory)
        return True

    def close_current(self, force: bool = False) -> bool:
        if self.project is None:
            return True

        if self.modified and not force:
            raise RuntimeError("Project has unsaved changes.")

        self.reset()
        return True

    def close(self, force: bool = False) -> bool:
        return self.close_current(force=force)

    def shutdown(self) -> bool:
        if self.project is None:
            return True

        if self.modified:
            self.autosave()

        return self.close_current(force=True)

    def validate_current(self) -> bool:
        if self.project is None:
            return False

        return ProjectValidator.validate_structure(self.project)

    def project_exists(self, path: str | Path) -> bool:
        project_path = Path(path)
        return (
            project_path.exists()
            and project_path.is_dir()
            and ProjectSerializer.exists(project_path)
        )

    def statistics(self) -> dict:
        root = self.project_root()
        return {
            "open": self.has_project(),
            "name": self.project_name(),
            "root": str(root) if root is not None else None,
            "modified": self.modified,
            "last_saved": self.last_saved,
            "has_recovery": self.has_recovery(),
            "backups": len(self.list_backups()),
        }

    def dispose(self) -> None:
        try:
            if self.project is not None and self.modified:
                self.autosave()
        except Exception:
            pass
        finally:
            self.reset()

    def __del__(self):
        try:
            self.dispose()
        except Exception:
            pass
