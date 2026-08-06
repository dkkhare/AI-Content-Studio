from __future__ import annotations

import json

import shutil

from pathlib import Path

from datetime import datetime


from backend.project.project import Project

from backend.project.exceptions import (
    ProjectSerializationError,
)



class ProjectSerializer:
    """
    Handles project persistence.

    Responsible for:
    - Saving project metadata
    - Loading projects
    - Creating backups

    Does not contain validation logic.
    """


    PROJECT_FILE = (
        "project.json"
    )



    # --------------------------------------------------
    # Project File Location
    # --------------------------------------------------

    @classmethod
    def project_file(
        cls,
        project_path: Path,
    ) -> Path:

        return (
            project_path
            /
            cls.PROJECT_FILE
        )



    # --------------------------------------------------
    # Serialize
    # --------------------------------------------------

    @classmethod
    def serialize(
        cls,
        project: Project,
    ) -> dict:

        return project.to_dict()



    # --------------------------------------------------
    # Deserialize
    # --------------------------------------------------

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> Project:

        try:

            return Project.from_dict(
                data
            )

        except Exception as exc:

            raise ProjectSerializationError(
                str(exc)
            )
    # --------------------------------------------------
    # Save Project
    # --------------------------------------------------

    @classmethod
    def save(
        cls,
        project: Project,
    ):

        try:

            project.initialize()


            file_path = cls.project_file(
                project.root
            )


            data = cls.serialize(
                project
            )


            temp_file = (
                file_path.with_suffix(
                    ".tmp"
                )
            )


            with open(
                temp_file,
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    data,
                    file,
                    indent=4,
                    ensure_ascii=False,
                )


            temp_file.replace(
                file_path
            )


        except Exception as exc:

            raise ProjectSerializationError(
                f"Unable to save project: {exc}"
            )



    # --------------------------------------------------
    # Load Project
    # --------------------------------------------------

    @classmethod
    def load(
        cls,
        project_path: Path,
    ) -> Project:

        try:

            file_path = cls.project_file(
                project_path
            )


            if not file_path.exists():

                raise ProjectSerializationError(
                    "project.json not found"
                )


            with open(
                file_path,
                "r",
                encoding="utf-8",
            ) as file:

                data = json.load(
                    file
                )


            project = cls.deserialize(
                data
            )


            return project


        except json.JSONDecodeError as exc:

            raise ProjectSerializationError(
                f"Invalid project file: {exc}"
            )


        except Exception as exc:

            raise ProjectSerializationError(
                f"Unable to load project: {exc}"
            )
    # --------------------------------------------------
    # Create Backup
    # --------------------------------------------------

    @classmethod
    def save_backup(
        cls,
        project: Project,
        backup_path: Path,
    ):

        try:

            project_file = cls.project_file(
                project.root
            )


            if not project_file.exists():

                cls.save(
                    project
                )


            backup_path = Path(
                backup_path
            )


            backup_path.mkdir(
                parents=True,
                exist_ok=True,
            )


            timestamp = datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )


            backup_file = (
                backup_path
                /
                f"project_backup_{timestamp}.json"
            )


            shutil.copy2(
                project_file,
                backup_file,
            )


            return backup_file


        except Exception as exc:

            raise ProjectSerializationError(
                f"Backup failed: {exc}"
            )



    # --------------------------------------------------
    # Restore Backup
    # --------------------------------------------------

    @classmethod
    def restore_backup(
        cls,
        backup_file: Path,
        project_path: Path,
    ):

        try:

            backup_file = Path(
                backup_file
            )


            if not backup_file.exists():

                raise ProjectSerializationError(
                    "Backup file does not exist"
                )


            project_path.mkdir(
                parents=True,
                exist_ok=True,
            )


            target = cls.project_file(
                project_path
            )


            shutil.copy2(
                backup_file,
                target,
            )


            return cls.load(
                project_path
            )


        except Exception as exc:

            raise ProjectSerializationError(
                f"Restore failed: {exc}"
            )



    # --------------------------------------------------
    # Utility
    # --------------------------------------------------

    @classmethod
    def exists(
        cls,
        project_path: Path,
    ) -> bool:

        return cls.project_file(
            project_path
        ).exists()



    @classmethod
    def delete(
        cls,
        project_path: Path,
    ):

        file_path = cls.project_file(
            project_path
        )


        if file_path.exists():

            file_path.unlink()