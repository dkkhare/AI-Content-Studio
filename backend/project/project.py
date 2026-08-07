from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_PROJECT_SETTINGS = {
    "autosave_interval_seconds": 300,
    "backup_retention": 10,
    "theme": "dark",
    "pipeline_ocr_enabled": True,
    "ocr_provider": "paddle",
    "pipeline_translation_enabled": False,
    "translation_provider": "google",
    "translation_api_key_env": "GOOGLE_TRANSLATE_API_KEY",
    "translation_source_language": "en",
    "translation_target_language": "en",
    "pipeline_ai_ocr_cleanup_enabled": False,
    "pipeline_ai_translation_enabled": False,
    "pipeline_ai_summary_enabled": False,
    "pipeline_ai_script_enabled": False,
    "pipeline_ai_subtitle_enabled": False,
    "ai_provider": "",
    "ai_model": "",
    "ai_source_language": "en",
    "ai_target_language": "en",
    "ai_summary_style": "concise",
    "ai_script_style": "natural narration",
    "ai_subtitle_language": "en",
    "pipeline_narration_enabled": True,
    "pipeline_video_enabled": False,
    "video_fps": 30,
    "video_seconds_per_image": 3.0,
    "ffmpeg_path": "",
}


@dataclass
class Project:
    """Core persisted project model."""

    name: str
    root: Path

    version: str = "1.0"
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    modified: str = field(default_factory=lambda: datetime.now().isoformat())

    description: str = ""
    author: str = ""

    pdf_file: str = ""
    language: str = "en"
    voice: str = ""
    output_directory: str = "output"
    auto_save: bool = True

    settings: dict[str, Any] = field(
        default_factory=lambda: dict(DEFAULT_PROJECT_SETTINGS)
    )

    status: str = "created"
    progress: int = 0
    error_message: str = ""

    ocr_file: str = ""
    translation_file: str = ""
    narration_file: str = ""
    audiobook_file: str = ""
    podcast_file: str = ""
    video_file: str = ""
    subtitle_file: str = ""
    cover_image: str = ""
    thumbnail: str = ""

    def project_path(self) -> Path:
        return self.root

    def output_path(self) -> Path:
        return self.root / self.output_directory

    def asset_path(self, filename: str) -> Path:
        return self.output_path() / filename

    def touch(self) -> None:
        self.modified = datetime.now().isoformat()

    def update_metadata(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.touch()

    def get_setting(self, key: str, default=None):
        if key in self.settings:
            return self.settings[key]
        if key in DEFAULT_PROJECT_SETTINGS:
            return DEFAULT_PROJECT_SETTINGS[key]
        return default

    def set_setting(self, key: str, value: Any) -> None:
        self.settings[key] = value
        self.touch()

    def update_settings(self, values: dict[str, Any]) -> None:
        self.settings.update(values)
        self.touch()

    def set_status(self, status: str) -> None:
        self.status = status
        self.touch()

    def set_progress(self, value: int) -> None:
        self.progress = max(0, min(100, int(value)))
        self.touch()

    def set_error(self, message: str) -> None:
        self.error_message = message
        self.status = "error"
        self.touch()

    def clear_error(self) -> None:
        self.error_message = ""
        self.touch()

    def start_processing(self, task: str) -> None:
        self.status = f"processing:{task}"
        self.progress = 0
        self.error_message = ""
        self.touch()

    def complete_processing(self) -> None:
        self.status = "completed"
        self.progress = 100
        self.touch()

    def reset_processing(self) -> None:
        self.status = "created"
        self.progress = 0
        self.error_message = ""
        self.touch()

    @staticmethod
    def asset_fields() -> tuple[str, ...]:
        return (
            "ocr_file",
            "translation_file",
            "narration_file",
            "audiobook_file",
            "podcast_file",
            "video_file",
            "subtitle_file",
            "cover_image",
            "thumbnail",
        )

    def add_output_file(self, file_type: str, file_path: str) -> None:
        if file_type not in self.asset_fields():
            raise ValueError(f"Unsupported asset type: {file_type}")
        setattr(self, file_type, file_path)
        self.touch()

    def register_asset(self, asset_name: str, file_path: str) -> None:
        if asset_name in self.asset_fields():
            setattr(self, asset_name, file_path)
            self.touch()

    def get_asset(self, asset_name: str):
        if hasattr(self, asset_name):
            return getattr(self, asset_name)
        return None

    def get_output_files(self) -> dict[str, str]:
        return {
            name: value
            for name in self.asset_fields()
            if (value := getattr(self, name, ""))
        }

    def asset_exists(self, asset_name: str) -> bool:
        file_path = self.get_asset(asset_name)
        if not file_path:
            return False
        path = Path(file_path)
        if not path.is_absolute():
            path = self.root / path
        return path.exists()

    def delete_output_files(self) -> None:
        for file_path in self.get_output_files().values():
            path = Path(file_path)
            if not path.is_absolute():
                path = self.root / path
            if path.exists() and path.is_file():
                path.unlink()
        self.touch()

    def initialize(self):
        self.root.mkdir(parents=True, exist_ok=True)
        self.output_path().mkdir(parents=True, exist_ok=True)
        self.touch()
        return self

    def is_ready(self) -> bool:
        return self.root.exists() and self.root.is_dir()

    def to_dict(self) -> dict:
        data = {}
        for key, value in self.__dict__.items():
            data[key] = str(value) if isinstance(value, Path) else value
        return data

    @classmethod
    def from_dict(cls, data: dict):
        values = dict(data)
        if "root" in values:
            values["root"] = Path(values["root"])

        settings = values.get("settings")
        if not isinstance(settings, dict):
            settings = {}
        merged_settings = dict(DEFAULT_PROJECT_SETTINGS)
        merged_settings.update(settings)
        values["settings"] = merged_settings

        return cls(**values)

    def __repr__(self) -> str:
        return (
            f"<Project name={self.name!r} root={str(self.root)!r} "
            f"status={self.status!r}>"
        )
