from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class FileEntry:
    """
    Metadata for a project file.
    """

    path: str

    created: str = field(

        default_factory=lambda:
        datetime.now().isoformat()

    )

    modified: str = field(

        default_factory=lambda:
        datetime.now().isoformat()

    )

    size: int = 0

    def exists(self):

        return Path(self.path).exists()

    def touch(self):

        self.modified = datetime.now().isoformat()

        p = Path(self.path)

        if p.exists():

            self.size = p.stat().st_size

    def to_dict(self):

        return {

            "path": self.path,

            "created": self.created,

            "modified": self.modified,

            "size": self.size,

        }

    @classmethod
    def from_dict(

        cls,

        data,

    ):

        return cls(

            path=data["path"],

            created=data.get(

                "created",

                datetime.now().isoformat(),

            ),

            modified=data.get(

                "modified",

                datetime.now().isoformat(),

            ),

            size=data.get(

                "size",

                0,

            ),

        )