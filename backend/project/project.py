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
    # Generated Assets
    # --------------------------------------------------

    ocr_file: str = ""

    translation_file: str = ""

    narration_file: str = ""

    audiobook_file: str = ""

    podcast_file: str = ""

    video_file: str = ""

    subtitle_file: str = ""

    cover_image: str = ""

    thumbnail: str = ""

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
    # Asset Helpers
    # --------------------------------------------------

    def has_pdf(self):

        return bool(self.pdf_file)

    def has_ocr(self):

        return bool(self.ocr_file)

    def has_translation(self):

        return bool(self.translation_file)

    def has_narration(self):

        return bool(self.narration_file)

    def has_audiobook(self):

        return bool(self.audiobook_file)

    def has_podcast(self):

        return bool(self.podcast_file)

    def has_video(self):

        return bool(self.video_file)

    def has_subtitles(self):

        return bool(self.subtitle_file)

    def has_cover(self):

        return bool(self.cover_image)

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

            "ocr_file": self.ocr_file,

            "translation_file": self.translation_file,

            "narration_file": self.narration_file,

            "audiobook_file": self.audiobook_file,

            "podcast_file": self.podcast_file,

            "video_file": self.video_file,

            "subtitle_file": self.subtitle_file,

            "cover_image": self.cover_image,

            "thumbnail": self.thumbnail,

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

            ocr_file=data.get(

                "ocr_file",

                "",

            ),

            translation_file=data.get(

                "translation_file",

                "",

            ),

            narration_file=data.get(

                "narration_file",

                "",

            ),

            audiobook_file=data.get(

                "audiobook_file",

                "",

            ),

            podcast_file=data.get(

                "podcast_file",

                "",

            ),

            video_file=data.get(

                "video_file",

                "",

            ),

            subtitle_file=data.get(

                "subtitle_file",

                "",

            ),

            cover_image=data.get(

                "cover_image",

                "",

            ),

            thumbnail=data.get(

                "thumbnail",

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

    # --------------------------------------------------
    # Version
    # --------------------------------------------------

    def is_version_supported(self) -> bool:

        return self.version.startswith("1.")

    # --------------------------------------------------
    # Metadata
    # --------------------------------------------------

    @property
    def metadata(self):

        return {

            "name": self.name,

            "author": self.author,

            "language": self.language,

            "voice": self.voice,

            "version": self.version,

            "created": self.created,

            "modified": self.modified,

        }