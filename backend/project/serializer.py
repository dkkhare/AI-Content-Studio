from __future__ import annotations

import json
from pathlib import Path

from backend.project.project import Project


class ProjectSerializer:

    FORMAT_VERSION = "1.0"

    @classmethod
    def save(

        cls,

        project: Project,

    ):

        project.touch()

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

    @classmethod
    def load(

        cls,

        root,

    ) -> Project:

        root = Path(root)

        data = json.loads(

            (root / "project.json").read_text(

                encoding="utf-8"

            )

        )

        data.pop(

            "format_version",

            None,

        )

        return Project.from_dict(

            root,

            data,

        )