from __future__ import annotations

import json
from pathlib import Path

from backend.project.project import Project


class ProjectSerializer:
    """
    Handles loading and saving project metadata.
    """

    @staticmethod
    def save(project: Project):

        project.touch()

        project.project_file.write_text(

            json.dumps(

                project.to_dict(),

                indent=4,

                ensure_ascii=False,

            ),

            encoding="utf-8",

        )

    @staticmethod
    def load(root: Path) -> Project:

        data = json.loads(

            (root / "project.json").read_text(

                encoding="utf-8"

            )

        )

        return Project.from_dict(

            root,

            data,

        )