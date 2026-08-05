from __future__ import annotations

import json
from pathlib import Path

from backend.project.exceptions import (
    InvalidProjectError,
)


class ProjectValidator:
    """
    Validates AI Content Studio projects.
    """

    REQUIRED_DIRECTORIES = [

        "pdf",

        "ocr",

        "tts",

        "translation",

        "video",

        "export",

        "cache",

    ]

    REQUIRED_FILES = [

        "project.json",

    ]

    @classmethod
    def validate(

        cls,

        root,

    ):

        root = Path(root)

        if not root.exists():

            raise InvalidProjectError(

                "Project directory does not exist."

            )

        if not root.is_dir():

            raise InvalidProjectError(

                "Invalid project directory."

            )

        for filename in cls.REQUIRED_FILES:

            if not (root / filename).exists():

                raise InvalidProjectError(

                    f"Missing {filename}"

                )

        for directory in cls.REQUIRED_DIRECTORIES:

            if not (root / directory).exists():

                raise InvalidProjectError(

                    f"Missing directory: {directory}"

                )

        try:

            json.loads(

                (root / "project.json").read_text(

                    encoding="utf-8"

                )

            )

        except Exception as exc:

            raise InvalidProjectError(

                f"Invalid project.json ({exc})"

            )

        return True