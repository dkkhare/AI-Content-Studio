from __future__ import annotations

from pathlib import Path
from typing import Any


class PipelineContext:
    """Shared mutable data passed between processing stages."""

    def __init__(self, project, data: dict[str, Any] | None = None):
        self.project = project
        self.data: dict[str, Any] = dict(data or {})

    @property
    def project_root(self) -> Path:
        return Path(self.project.root).resolve()

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> Any:
        self.data[key] = value
        return value

    def update(self, values: dict[str, Any]) -> None:
        self.data.update(values)

    def path(self, *parts: str, create_parent: bool = False) -> Path:
        value = self.project_root.joinpath(*parts)
        if create_parent:
            value.parent.mkdir(parents=True, exist_ok=True)
        return value

    def write_text_atomic(self, relative_path: str, text: str) -> Path:
        target = self.path(relative_path, create_parent=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(str(text), encoding="utf-8")
        temporary.replace(target)
        return target

    @property
    def ocr_text(self) -> str:
        return str(self.get("ocr_text", ""))

    @ocr_text.setter
    def ocr_text(self, value: str) -> None:
        self.set("ocr_text", value)

    @property
    def cleaned_text(self) -> str:
        return str(self.get("cleaned_text", ""))

    @cleaned_text.setter
    def cleaned_text(self, value: str) -> None:
        self.set("cleaned_text", value)

    @property
    def audio_file(self) -> str:
        return str(self.get("audio_file", ""))

    @audio_file.setter
    def audio_file(self, value: str) -> None:
        self.set("audio_file", value)

    @property
    def avatar_video(self) -> str:
        return str(self.get("avatar_video", ""))

    @avatar_video.setter
    def avatar_video(self, value: str) -> None:
        self.set("avatar_video", value)

    @property
    def subtitle_file(self) -> str:
        return str(self.get("subtitle_file", ""))

    @subtitle_file.setter
    def subtitle_file(self, value: str) -> None:
        self.set("subtitle_file", value)

    @property
    def final_video(self) -> str:
        return str(self.get("final_video", ""))

    @final_video.setter
    def final_video(self, value: str) -> None:
        self.set("final_video", value)
