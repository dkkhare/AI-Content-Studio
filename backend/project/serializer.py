from __future__ import annotations

import json
from pathlib import Path

from backend.project.project import Project


class ProjectSerializer:
    """
    Handles serialization and deserialization of Project objects.
    """

    FORMAT_VERSION = "1.0"

    @classmethod
    def save(
        cls,
        project: Project,
    ) -> Path:

        project.touch()

        project.create_directories()

        data = project.to_dict()

        data["format_version"] = cls.FORMAT_VERSION

        project.project_file.write_text(

            json.dumps(
                data,
                indent=4,
                ensure_ascii=False,
            ),

            encoding="utf-8",

        )

        return project.project_file

    @classmethod
    def load(
        cls,
        root,
    ) -> Project:

        root = Path(root)

        project_file = root / "project.json"

        if not project_file.exists():

            raise FileNotFoundError(

                f"Project file not found: {project_file}"

            )

        data = json.loads(

            project_file.read_text(

                encoding="utf-8"

            )

        )

        version = data.get(

            "format_version",

            "1.0",

        )

        if not version.startswith("1."):

            raise RuntimeError(

                f"Unsupported project format: {version}"

            )

        data.pop(

            "format_version",

            None,

        )

        return Project.from_dict(

            root,

            data,

        )

    @classmethod
    def exists(
        cls,
        root,
    ) -> bool:

        return (

            Path(root) /

            "project.json"

        ).exists()

    @classmethod
    def create(
        cls,
        project: Project,
    ) -> Project:

        project.create_directories()

        cls.save(project)

        return project