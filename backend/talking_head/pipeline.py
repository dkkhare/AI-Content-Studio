from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import Event
from typing import Callable

from backend.tts.adapters import GenerationRequest


class PipelineCancelled(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class SadTalkerConfig:
    repository: Path
    python: str = "python"
    size: int = 256
    preprocess: str = "crop"
    still: bool = False
    enhancer: str = ""

    def validate(self) -> "SadTalkerConfig":
        if not (self.repository / "inference.py").is_file():
            raise FileNotFoundError(
                f"SadTalker inference.py not found under {self.repository}"
            )
        if self.size not in {256, 512}:
            raise ValueError("SadTalker size must be 256 or 512.")
        if self.preprocess not in {"crop", "resize", "full", "extcrop", "extfull"}:
            raise ValueError(f"Unsupported SadTalker preprocess mode: {self.preprocess}")
        return self


@dataclass(frozen=True, slots=True)
class PodcastRequest:
    script: str
    portrait: Path
    reference_audio: Path
    reference_text: str
    output: Path
    work_directory: Path
    target_minutes: float = 15.0
    segment_seconds: float = 45.0

    def validate(self) -> "PodcastRequest":
        if not self.script.strip():
            raise ValueError("Podcast script is required.")
        if not self.portrait.is_file():
            raise FileNotFoundError(f"Writer portrait not found: {self.portrait}")
        if self.portrait.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            raise ValueError("Writer portrait must be PNG, JPEG, or WebP.")
        if not self.reference_audio.is_file():
            raise FileNotFoundError(
                f"Reference voice sample not found: {self.reference_audio}"
            )
        if not self.reference_text.strip():
            raise ValueError("The exact voice-sample transcript is required.")
        if self.output.suffix.lower() != ".mp4":
            raise ValueError("Podcast output must use the .mp4 extension.")
        if not 1 <= self.target_minutes <= 180:
            raise ValueError("Target duration must be between 1 and 180 minutes.")
        if not 15 <= self.segment_seconds <= 90:
            raise ValueError("Segment duration must be between 15 and 90 seconds.")
        return self


@dataclass(frozen=True, slots=True)
class SegmentRecord:
    index: int
    text: str
    audio: str
    video: str
    status: str = "complete"


@dataclass(frozen=True, slots=True)
class PodcastResult:
    output: str
    manifest: str
    segments: tuple[SegmentRecord, ...]
    resumed_segments: int = 0


def split_script(
    text: str, *, segment_seconds: float = 45.0, characters_per_second: float = 14.0
) -> list[str]:
    """Split at sentence boundaries while keeping chunks suitable for 4 GB GPUs."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []
    limit = max(1, round(segment_seconds * characters_per_second))
    sentences = [
        value.strip()
        for value in re.split(r"(?<=[.!?।॥])\s+", cleaned)
        if value.strip()
    ]
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(sentence) > limit:
            words = sentence.split()
            for word in words:
                candidate = f"{current} {word}".strip()
                if current and len(candidate) > limit:
                    chunks.append(current)
                    current = word
                else:
                    current = candidate
            continue
        candidate = f"{current} {sentence}".strip()
        if current and len(candidate) > limit:
            chunks.append(current)
            current = sentence
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


class SadTalkerAdapter:
    """Bounded subprocess adapter; SadTalker remains an isolated optional runtime."""

    def __init__(
        self,
        config: SadTalkerConfig,
        *,
        runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    ):
        self.config = config
        self.runner = runner

    def generate(
        self, portrait: Path, audio: Path, output: Path, *, cancel_event: Event | None = None
    ) -> Path:
        self.config.validate()
        if cancel_event and cancel_event.is_set():
            raise PipelineCancelled("Talking-head generation cancelled.")
        output.parent.mkdir(parents=True, exist_ok=True)
        result_dir = output.parent / f".{output.stem}-sadtalker"
        if result_dir.exists():
            shutil.rmtree(result_dir)
        result_dir.mkdir(parents=True)
        command = [
            self.config.python,
            "inference.py",
            "--driven_audio",
            str(audio.resolve()),
            "--source_image",
            str(portrait.resolve()),
            "--result_dir",
            str(result_dir.resolve()),
            "--size",
            str(self.config.size),
            "--preprocess",
            self.config.preprocess,
        ]
        if self.config.still:
            command.append("--still")
        if self.config.enhancer:
            command.extend(["--enhancer", self.config.enhancer])
        completed = self.runner(
            command,
            cwd=str(self.config.repository.resolve()),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if completed.returncode:
            detail = (completed.stderr or completed.stdout or "").strip()
            raise RuntimeError(
                f"SadTalker failed with exit code {completed.returncode}: {detail[-2000:]}"
            )
        candidates = sorted(result_dir.rglob("*.mp4"), key=lambda path: path.stat().st_mtime)
        if not candidates:
            raise RuntimeError("SadTalker completed without producing an MP4 file.")
        temporary = output.with_suffix(".partial.mp4")
        shutil.copy2(candidates[-1], temporary)
        temporary.replace(output)
        shutil.rmtree(result_dir, ignore_errors=True)
        return output.resolve()


class LongFormTalkingHeadPipeline:
    """Resumable F5-TTS -> SadTalker -> FFmpeg pipeline for long podcasts."""

    def __init__(
        self,
        *,
        tts,
        sadtalker: SadTalkerAdapter,
        ffmpeg: str = "ffmpeg",
        runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    ):
        self.tts = tts
        self.sadtalker = sadtalker
        self.ffmpeg = ffmpeg
        self.runner = runner

    @staticmethod
    def _fingerprint(request: PodcastRequest, chunks: list[str]) -> str:
        payload = {
            "portrait": str(request.portrait.resolve()),
            "reference_audio": str(request.reference_audio.resolve()),
            "reference_text": request.reference_text,
            "chunks": chunks,
        }
        return hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _write_json(path: Path, value: dict) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        temporary.replace(path)

    def _concat(self, videos: list[Path], output: Path) -> None:
        concat_file = output.parent / ".talking-head-concat.txt"
        concat_file.write_text(
            "".join(f"file '{str(path.resolve()).replace(chr(39), chr(39) * 2)}'\n" for path in videos),
            encoding="utf-8",
        )
        partial = output.with_suffix(".partial.mp4")
        command = [
            self.ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
            "-c", "copy", "-movflags", "+faststart", str(partial),
        ]
        completed = self.runner(
            command, capture_output=True, text=True, encoding="utf-8",
            errors="replace", check=False
        )
        concat_file.unlink(missing_ok=True)
        if completed.returncode or not partial.is_file():
            partial.unlink(missing_ok=True)
            detail = (completed.stderr or completed.stdout or "").strip()
            raise RuntimeError(f"FFmpeg could not assemble podcast: {detail[-2000:]}")
        partial.replace(output)

    def run(
        self,
        request: PodcastRequest,
        *,
        progress: Callable[[float, str], None] | None = None,
        cancel_event: Event | None = None,
    ) -> PodcastResult:
        request.validate()
        chunks = split_script(request.script, segment_seconds=request.segment_seconds)
        if not chunks:
            raise ValueError("Podcast script did not contain usable text.")
        request.work_directory.mkdir(parents=True, exist_ok=True)
        request.output.parent.mkdir(parents=True, exist_ok=True)
        manifest_path = request.work_directory / "manifest.json"
        fingerprint = self._fingerprint(request, chunks)
        previous = {}
        if manifest_path.is_file():
            try:
                previous = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                previous = {}
        if previous.get("fingerprint") != fingerprint:
            previous = {}
        records: list[SegmentRecord] = []
        resumed = 0
        total = len(chunks)
        for index, text in enumerate(chunks, 1):
            if cancel_event and cancel_event.is_set():
                raise PipelineCancelled("Talking-head generation cancelled.")
            stem = f"segment-{index:04d}"
            audio = request.work_directory / f"{stem}.wav"
            video = request.work_directory / f"{stem}.mp4"
            old = next(
                (item for item in previous.get("segments", []) if item.get("index") == index),
                None,
            )
            if old and old.get("text") == text and audio.is_file() and video.is_file():
                resumed += 1
            else:
                result = self.tts.generate(
                    GenerationRequest(
                        reference_audio=str(request.reference_audio),
                        reference_text=request.reference_text,
                        generation_text=text,
                        output_audio=str(audio),
                    )
                )
                generated_audio = Path(result.output_audio)
                if generated_audio.resolve() != audio.resolve():
                    shutil.copy2(generated_audio, audio)
                self.sadtalker.generate(
                    request.portrait, audio, video, cancel_event=cancel_event
                )
            record = SegmentRecord(index, text, str(audio), str(video))
            records.append(record)
            self._write_json(
                manifest_path,
                {
                    "version": 1,
                    "fingerprint": fingerprint,
                    "target_minutes": request.target_minutes,
                    "segment_seconds": request.segment_seconds,
                    "segments": [asdict(item) for item in records],
                },
            )
            if progress:
                progress(index * 90.0 / total, f"Generated segment {index} of {total}")
        self._concat([Path(item.video) for item in records], request.output)
        if progress:
            progress(100.0, "Talking-head podcast complete")
        return PodcastResult(
            str(request.output.resolve()), str(manifest_path.resolve()),
            tuple(records), resumed
        )
