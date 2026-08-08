from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class VideoSpec:
    width: int = 1920
    height: int = 1080
    fps: int = 30
    duration_ms: int = 0

    def __post_init__(self):
        if self.width < 16 or self.height < 16:
            raise ValueError("Video dimensions must be at least 16x16.")
        if self.width % 2 or self.height % 2:
            raise ValueError("Video dimensions must be even for broad codec support.")
        if not 1 <= self.fps <= 120:
            raise ValueError("Frame rate must be between 1 and 120 fps.")
        if self.duration_ms <= 0:
            raise ValueError("Video duration must be positive.")

    @property
    def frame_count(self) -> int:
        return (self.duration_ms * self.fps + 999) // 1000


@dataclass(frozen=True)
class MediaAsset:
    kind: str
    path: str

    def __post_init__(self):
        if self.kind not in {"image", "video", "audio", "subtitles"}:
            raise ValueError(f"Unsupported media kind: {self.kind}")
        if not str(self.path).strip():
            raise ValueError("Media path is required.")


@dataclass(frozen=True)
class CompositionManifest:
    spec: VideoSpec
    visual: MediaAsset
    audio: MediaAsset
    subtitles: MediaAsset | None = None

    def __post_init__(self):
        if self.visual.kind not in {"image", "video"}:
            raise ValueError("The visual asset must be an image or video.")
        if self.audio.kind != "audio":
            raise ValueError("The audio asset must have kind 'audio'.")
        if self.subtitles is not None and self.subtitles.kind != "subtitles":
            raise ValueError("The subtitle asset must have kind 'subtitles'.")

    def to_dict(self) -> dict:
        return asdict(self)

    def write(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(target)
        return target


class VideoComposer:
    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
    VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm"}
    AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}
    SUBTITLE_EXTENSIONS = {".srt", ".vtt"}

    @classmethod
    def _asset(cls, kind: str, value: str | Path, extensions: set[str]) -> MediaAsset:
        path = Path(value).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"{kind.title()} asset does not exist: {path}")
        if path.suffix.lower() not in extensions:
            raise ValueError(f"Unsupported {kind} format: {path.suffix or '<none>'}")
        return MediaAsset(kind, str(path))

    def plan(
        self,
        *,
        visual: str | Path,
        audio: str | Path,
        duration_seconds: float,
        subtitles: str | Path | None = None,
        width: int = 1920,
        height: int = 1080,
        fps: int = 30,
    ) -> CompositionManifest:
        duration_ms = round(float(duration_seconds) * 1000)
        spec = VideoSpec(width, height, fps, duration_ms)
        visual_path = Path(visual)
        visual_extensions = (
            self.IMAGE_EXTENSIONS
            if visual_path.suffix.lower() in self.IMAGE_EXTENSIONS
            else self.VIDEO_EXTENSIONS
        )
        subtitle_asset = (
            self._asset("subtitles", subtitles, self.SUBTITLE_EXTENSIONS)
            if subtitles is not None
            else None
        )
        return CompositionManifest(
            spec=spec,
            visual=self._asset(
                "image" if visual_extensions is self.IMAGE_EXTENSIONS else "video",
                visual,
                visual_extensions,
            ),
            audio=self._asset("audio", audio, self.AUDIO_EXTENSIONS),
            subtitles=subtitle_asset,
        )
