from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExportPreset:
    name: str
    assets: tuple[str, ...]
    required: tuple[str, ...] = ()

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("Export preset name is required.")
        if not self.assets:
            raise ValueError("Export preset must include at least one asset.")
        if len(set(self.assets)) != len(self.assets):
            raise ValueError("Export preset assets must be unique.")
        if not set(self.required).issubset(self.assets):
            raise ValueError("Required assets must be included by the preset.")


PRESETS = {
    "video": ExportPreset(
        "video",
        ("video_file", "subtitle_file", "thumbnail"),
        ("video_file",),
    ),
    "publishing": ExportPreset(
        "publishing",
        ("video_file", "subtitle_file", "thumbnail", "cover_image"),
        ("video_file",),
    ),
    "archive": ExportPreset(
        "archive",
        (
            "video_file",
            "subtitle_file",
            "narration_file",
            "audiobook_file",
            "podcast_file",
            "translation_file",
            "ocr_file",
            "thumbnail",
            "cover_image",
        ),
    ),
}


@dataclass(frozen=True)
class ExportAsset:
    role: str
    filename: str
    size: int
    sha256: str

    @classmethod
    def from_file(cls, role: str, path: str | Path, filename: str):
        source = Path(path)
        digest = hashlib.sha256()
        with source.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return cls(role, filename, source.stat().st_size, digest.hexdigest())


@dataclass(frozen=True)
class ExportManifest:
    project: str
    preset: str
    assets: tuple[ExportAsset, ...]

    def __post_init__(self):
        if not self.project.strip():
            raise ValueError("Export project name is required.")
        if not self.preset.strip():
            raise ValueError("Export preset name is required.")

    def to_dict(self):
        return asdict(self)

    def write(self, path: str | Path):
        target = Path(path)
        target.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return target
