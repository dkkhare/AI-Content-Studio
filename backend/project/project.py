from __future__ import annotations

from dataclasses import (
    dataclass,
    field,
)

from datetime import datetime

from pathlib import Path



@dataclass
class Project:
    """
    Core project data model.

    Stores:
    - project metadata
    - source files
    - generated assets
    - processing state

    Persistence is handled by ProjectSerializer.
    Validation is handled by ProjectValidator.
    """


    name: str

    root: Path


    version: str = "1.0"


    created: str = field(
        default_factory=lambda:
        datetime.now().isoformat()
    )


    modified: str = field(
        default_factory=lambda:
        datetime.now().isoformat()
    )


    description: str = ""


    author: str = ""


    # --------------------------------------------------
    # Source Content
    # --------------------------------------------------

    pdf_file: str = ""

    language: str = "en"

    voice: str = ""


    output_directory: str = "output"


    auto_save: bool = True


    # --------------------------------------------------
    # Processing State
    # --------------------------------------------------

    status: str = "created"


    progress: int = 0


    error_message: str = ""


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
    # Path Helpers
    # --------------------------------------------------

    def project_path(
        self,
    ) -> Path:

        return self.root



    def output_path(
        self,
    ) -> Path:

        return (
            self.root
            /
            self.output_directory
        )



    def asset_path(
        self,
        filename: str,
    ) -> Path:

        return (
            self.output_path()
            /
            filename
        )



    # --------------------------------------------------
    # Metadata Updates
    # --------------------------------------------------

    def touch(
        self,
    ):

        self.modified = (
            datetime.now()
            .isoformat()
        )



    def update_metadata(
        self,
        **kwargs,
    ):

        for key, value in kwargs.items():

            if hasattr(
                self,
                key,
            ):

                setattr(
                    self,
                    key,
                    value,
                )


        self.touch()



    # --------------------------------------------------
    # Processing State
    # --------------------------------------------------

    def set_status(
        self,
        status: str,
    ):

        self.status = status

        self.touch()



    def set_progress(
        self,
        value: int,
    ):

        self.progress = max(
            0,
            min(
                100,
                value,
            ),
        )


        self.touch()



    def set_error(
        self,
        message: str,
    ):

        self.error_message = message

        self.status = "error"

        self.touch()



    def clear_error(
        self,
    ):

        self.error_message = ""

        self.touch()
    # --------------------------------------------------
    # Asset Management
    # --------------------------------------------------

    def add_output_file(
        self,
        file_type: str,
        file_path: str,
    ):

        """
        Register generated pipeline output.

        Example:
        add_output_file(
            "video_file",
            "output/video.mp4"
        )
        """

        allowed_assets = [
            "ocr_file",
            "translation_file",
            "narration_file",
            "audiobook_file",
            "podcast_file",
            "video_file",
            "subtitle_file",
            "cover_image",
            "thumbnail",
        ]


        if file_type not in allowed_assets:

            raise ValueError(
                f"Unsupported asset type: {file_type}"
            )


        setattr(
            self,
            file_type,
            file_path,
        )


        self.touch()



    def get_output_files(
        self,
    ) -> dict:

        assets = {}

        fields = [
            "ocr_file",
            "translation_file",
            "narration_file",
            "audiobook_file",
            "podcast_file",
            "video_file",
            "subtitle_file",
            "cover_image",
            "thumbnail",
        ]


        for field_name in fields:

            value = getattr(
                self,
                field_name,
            )


            if value:

                assets[field_name] = value


        return assets



    # --------------------------------------------------
    # Pipeline Helpers
    # --------------------------------------------------

    def start_processing(
        self,
        task: str,
    ):

        self.status = (
            f"processing:{task}"
        )

        self.progress = 0

        self.error_message = ""

        self.touch()



    def complete_processing(
        self,
    ):

        self.status = "completed"

        self.progress = 100

        self.touch()



    def reset_processing(
        self,
    ):

        self.status = "created"

        self.progress = 0

        self.error_message = ""

        self.touch()



    # --------------------------------------------------
    # Project Lifecycle
    # --------------------------------------------------

    def is_ready(
        self,
    ) -> bool:

        return (
            self.root.exists()
            and self.root.is_dir()
        )



    def delete_output_files(
        self,
    ):

        for file_path in (
            self.get_output_files()
            .values()
        ):

            path = Path(
                file_path
            )


            if path.exists():

                path.unlink()



        self.touch()
    # --------------------------------------------------
    # Project Initialization
    # --------------------------------------------------

    def initialize(
        self,
    ):

        self.root.mkdir(
            parents=True,
            exist_ok=True,
        )


        self.output_path().mkdir(
            parents=True,
            exist_ok=True,
        )


        self.touch()


        return self



    # --------------------------------------------------
    # Asset Registration
    # --------------------------------------------------

    def register_asset(
        self,
        asset_name: str,
        file_path: str,
    ):

        if hasattr(
            self,
            asset_name,
        ):

            setattr(
                self,
                asset_name,
                file_path,
            )


            self.touch()



    def get_asset(
        self,
        asset_name: str,
    ):

        if hasattr(
            self,
            asset_name,
        ):

            return getattr(
                self,
                asset_name,
            )


        return None



    # --------------------------------------------------
    # File Checks
    # --------------------------------------------------

    def asset_exists(
        self,
        asset_name: str,
    ) -> bool:

        file_path = self.get_asset(
            asset_name
        )


        if not file_path:

            return False


        return Path(
            file_path
        ).exists()



    # --------------------------------------------------
    # Serialization Helpers
    # --------------------------------------------------

    def to_dict(
        self,
    ) -> dict:

        data = {}


        for key, value in self.__dict__.items():

            if isinstance(
                value,
                Path,
            ):

                data[key] = str(
                    value
                )

            else:

                data[key] = value


        return data



    @classmethod
    def from_dict(
        cls,
        data: dict,
    ):

        if "root" in data:

            data["root"] = Path(
                data["root"]
            )


        return cls(
            **data
        )



    # --------------------------------------------------
    # Debug
    # --------------------------------------------------

    def __repr__(
        self,
    ):

        return (
            f"<Project "
            f"name={self.name!r} "
            f"root={str(self.root)!r} "
            f"status={self.status!r}>"
        )