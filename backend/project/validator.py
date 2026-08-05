from pathlib import Path

from backend.project.exceptions import (
    InvalidProjectError,
)


class ProjectValidator:
    """
    Validates AI Content Studio projects.
    """

    REQUIRED = [

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

                "Project folder does not exist."

            )

        for file in cls.REQUIRED:

            if not (root / file).exists():

                raise InvalidProjectError(

                    f"Missing {file}"

                )

        return True