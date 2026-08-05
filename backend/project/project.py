from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class Project:

    name: str

    root: Path

    version: str = "1.0"

    created: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )

    modified: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )

    description: str = ""

    author: str = ""

    pdf_file: str = ""

    language: str = "en"

    voice: str = ""

    output_directory: str = "output"

    auto_save: bool = True
    # --------------------------------------------------
    # Directories
    # --------------------------------------------------

    @property
    def pdf_dir(self) -> Path:

        return self.root / "pdf"

    @property
    def ocr_dir(self) -> Path:

        return self.root / "ocr"

    @property
    def tts_dir(self) -> Path:

        return self.root / "tts"

    @property
    def translation_dir(self) -> Path:

        return self.root / "translation"

    @property
    def video_dir(self) -> Path:

        return self.root / "video"

    @property
    def export_dir(self) -> Path:

        return self.root / "export"

    @property
    def cache_dir(self) -> Path:

        return self.root / "cache"
    # --------------------------------------------------
    # Files
    # --------------------------------------------------

    @property
    def project_file(self) -> Path:

        return self.root / "project.json"

    @property
    def metadata_file(self) -> Path:

        return self.root / "metadata.json"
    # --------------------------------------------------
    # Utilities
    # --------------------------------------------------

    def touch(self):

        self.modified = datetime.now().isoformat()

    def exists(self) -> bool:

        return self.project_file.exists()

    def create_directories(self):

        directories = [

            self.root,

            self.pdf_dir,

            self.ocr_dir,

            self.tts_dir,

            self.translation_dir,

            self.video_dir,

            self.export_dir,

            self.cache_dir,

        ]

        for directory in directories:

            directory.mkdir(

                parents=True,

                exist_ok=True,

            )
    # --------------------------------------------------
    # Serialization
    # --------------------------------------------------

    def to_dict(self):

        return {

            "name": self.name,

            "version": self.version,

            "created": self.created,

            "modified": self.modified,

            "description": self.description,

            "author": self.author,

            "pdf_file": self.pdf_file,

            "language": self.language,

            "voice": self.voice,

            "output_directory": self.output_directory,

            "auto_save": self.auto_save,

        }
    @classmethod
    def from_dict(

        cls,

        root,

        data,

    ):

        return cls(

            name=data.get(

                "name",

                "",

            ),

            root=Path(root),

            version=data.get(

                "version",

                "1.0",

            ),

            created=data.get(

                "created",

                datetime.now().isoformat(),

            ),

            modified=data.get(

                "modified",

                datetime.now().isoformat(),

            ),

            description=data.get(

                "description",

                "",

            ),

            author=data.get(

                "author",

                "",

            ),

            pdf_file=data.get(

                "pdf_file",

                "",

            ),

            language=data.get(

                "language",

                "en",

            ),

            voice=data.get(

                "voice",

                "",

            ),

            output_directory=data.get(

                "output_directory",

                "output",

            ),

            auto_save=data.get(

                "auto_save",

                True,

            ),

        )