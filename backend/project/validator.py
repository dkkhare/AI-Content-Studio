from __future__ import annotations

from pathlib import Path

from backend.project.project import Project

from backend.project.exceptions import (
    ProjectValidationError,
)



class ProjectValidator:
    """
    Validates project structure and data.

    Validation only.
    No saving or loading logic.
    """



    # --------------------------------------------------
    # Main Validation
    # --------------------------------------------------

    @classmethod
    def validate_structure(
        cls,
        project: Project,
    ) -> bool:

        try:

            cls.validate_root(
                project
            )


            cls.validate_metadata(
                project
            )


            return True


        except Exception as exc:

            raise ProjectValidationError(
                str(exc)
            )



    # --------------------------------------------------
    # Root Validation
    # --------------------------------------------------

    @classmethod
    def validate_root(
        cls,
        project: Project,
    ):

        if not project.root:

            raise ProjectValidationError(
                "Project root is missing"
            )


        root = Path(
            project.root
        )


        if not root.exists():

            raise ProjectValidationError(
                "Project directory does not exist"
            )


        if not root.is_dir():

            raise ProjectValidationError(
                "Project root is not a directory"
            )



    # --------------------------------------------------
    # Metadata Validation
    # --------------------------------------------------

    @classmethod
    def validate_metadata(
        cls,
        project: Project,
    ):

        if not project.name:

            raise ProjectValidationError(
                "Project name is required"
            )


        if not project.version:

            raise ProjectValidationError(
                "Project version is missing"
            )
    # --------------------------------------------------
    # Output Directory Validation
    # --------------------------------------------------

    @classmethod
    def validate_output_directory(
        cls,
        project: Project,
    ):

        output = (
            project.root
            /
            project.output_directory
        )


        if not output.exists():

            output.mkdir(
                parents=True,
                exist_ok=True,
            )


        if not output.is_dir():

            raise ProjectValidationError(
                "Output path is not a directory"
            )



    # --------------------------------------------------
    # Source File Validation
    # --------------------------------------------------

    @classmethod
    def validate_source_files(
        cls,
        project: Project,
    ):

        if not project.pdf_file:

            return True


        pdf = Path(
            project.pdf_file
        )


        if not pdf.exists():

            raise ProjectValidationError(
                "Source PDF file does not exist"
            )


        return True



    # --------------------------------------------------
    # Generated Asset Validation
    # --------------------------------------------------

    @classmethod
    def validate_assets(
        cls,
        project: Project,
    ):

        assets = [
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


        missing = []


        for asset in assets:

            value = getattr(
                project,
                asset,
                "",
            )


            if value:

                if not Path(
                    value
                ).exists():

                    missing.append(
                        asset
                    )


        if missing:

            raise ProjectValidationError(
                "Missing assets: "
                +
                ", ".join(missing)
            )


        return True



    # --------------------------------------------------
    # Ready Check
    # --------------------------------------------------

    @classmethod
    def is_ready(
        cls,
        project: Project,
    ) -> bool:

        try:

            cls.validate_structure(
                project
            )


            cls.validate_output_directory(
                project
            )


            cls.validate_source_files(
                project
            )


            return True


        except ProjectValidationError:

            return False
    # --------------------------------------------------
    # Complete Validation
    # --------------------------------------------------

    @classmethod
    def validate_complete(
        cls,
        project: Project,
    ) -> bool:

        cls.validate_structure(
            project
        )

        cls.validate_output_directory(
            project
        )

        cls.validate_source_files(
            project
        )

        cls.validate_assets(
            project
        )

        return True



    # --------------------------------------------------
    # Validation Report
    # --------------------------------------------------

    @classmethod
    def validation_report(
        cls,
        project: Project,
    ) -> dict:

        report = {
            "valid": True,
            "errors": [],
        }


        checks = (
            cls.validate_structure,
            cls.validate_output_directory,
            cls.validate_source_files,
            cls.validate_assets,
        )


        for check in checks:

            try:

                check(
                    project
                )

            except ProjectValidationError as exc:

                report["valid"] = False

                report["errors"].append(
                    str(exc)
                )


        return report



    # --------------------------------------------------
    # Helper Methods
    # --------------------------------------------------

    @classmethod
    def project_exists(
        cls,
        path: str | Path,
    ) -> bool:

        path = Path(
            path
        )

        return (
            path.exists()
            and
            path.is_dir()
        )



    @classmethod
    def project_file_exists(
        cls,
        path: str | Path,
    ) -> bool:

        path = Path(
            path
        )

        return (
            path
            /
            "project.json"
        ).exists()



    @classmethod
    def can_open(
        cls,
        path: str | Path,
    ) -> bool:

        return (
            cls.project_exists(
                path
            )
            and
            cls.project_file_exists(
                path
            )
        )



    # --------------------------------------------------
    # Utility
    # --------------------------------------------------

    @classmethod
    def ensure_directory(
        cls,
        path: str | Path,
    ) -> Path:

        directory = Path(
            path
        )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        return directory