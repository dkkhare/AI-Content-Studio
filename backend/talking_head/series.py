from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import Event
from typing import Callable

from .episodes import SeriesPlan, SourceBlock, plan_episodes
from .pipeline import PipelineCancelled, PodcastRequest


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return cleaned[:48] or "episode"


@dataclass(frozen=True, slots=True)
class SeriesRequest:
    blocks: tuple[SourceBlock, ...]
    portrait: Path
    reference_audio: Path
    reference_text: str
    output_directory: Path
    work_directory: Path
    episode_minutes: float = 15.0
    segment_seconds: float = 45.0
    words_per_minute: float = 140.0
    rights_confirmed: bool = False

    def validate(self) -> "SeriesRequest":
        if not self.blocks:
            raise ValueError("The complete ordered book content is required.")
        if not self.portrait.is_file():
            raise FileNotFoundError(f"Writer portrait not found: {self.portrait}")
        if not self.reference_audio.is_file():
            raise FileNotFoundError(f"Voice sample not found: {self.reference_audio}")
        if not self.reference_text.strip():
            raise ValueError("The exact voice-sample transcript is required.")
        if not self.rights_confirmed:
            raise ValueError(
                "Confirm permission to use the book, writer image, and writer voice."
            )
        if not 15 <= self.segment_seconds <= 90:
            raise ValueError("Render segment duration must be between 15 and 90 seconds.")
        return self


@dataclass(frozen=True, slots=True)
class EpisodeOutput:
    number: int
    title: str
    output: str
    estimated_seconds: float
    source_ids: tuple[str, ...]
    sha256: str
    status: str = "complete"


@dataclass(frozen=True, slots=True)
class SeriesResult:
    output_directory: str
    manifest: str
    playlist: str
    episodes: tuple[EpisodeOutput, ...]
    resumed_episodes: int


class TalkingHeadSeriesPipeline:
    """Generate a complete, resumable set of lip-synced book episodes."""

    def __init__(self, episode_pipeline):
        self.episode_pipeline = episode_pipeline

    @staticmethod
    def _atomic_json(path: Path, data: dict) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        temporary.replace(path)

    @staticmethod
    def _fingerprint(request: SeriesRequest, plan: SeriesPlan) -> str:
        value = {
            "sources": list(plan.source_hashes),
            "source_order": list(plan.source_order),
            "portrait": _sha256(request.portrait),
            "reference_audio": _sha256(request.reference_audio),
            "reference_text": request.reference_text.strip(),
            "episode_minutes": request.episode_minutes,
            "segment_seconds": request.segment_seconds,
            "words_per_minute": request.words_per_minute,
        }
        return hashlib.sha256(
            json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _source_ids(episode) -> tuple[str, ...]:
        values: list[str] = []
        for fragment in episode.fragments:
            if fragment.source_id not in values:
                values.append(fragment.source_id)
        return tuple(values)

    @staticmethod
    def _valid_previous(item: dict, output: Path) -> bool:
        if item.get("status") != "complete" or not output.is_file():
            return False
        expected = str(item.get("sha256") or "")
        return bool(expected) and _sha256(output) == expected

    def run(
        self,
        request: SeriesRequest,
        *,
        progress: Callable[[float, str], None] | None = None,
        cancel_event: Event | None = None,
    ) -> SeriesResult:
        request.validate()
        plan = plan_episodes(
            request.blocks,
            target_minutes=request.episode_minutes,
            words_per_minute=request.words_per_minute,
        )
        plan.validate_coverage()
        request.output_directory.mkdir(parents=True, exist_ok=True)
        request.work_directory.mkdir(parents=True, exist_ok=True)
        manifest = request.output_directory / "series.json"
        playlist = request.output_directory / "playlist.m3u8"
        fingerprint = self._fingerprint(request, plan)
        previous: dict = {}
        if manifest.is_file():
            try:
                previous = json.loads(manifest.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                previous = {}
        if previous.get("fingerprint") != fingerprint:
            previous = {}
        previous_items = {
            int(item["number"]): item
            for item in previous.get("episodes", [])
            if isinstance(item, dict) and str(item.get("number", "")).isdigit()
        }

        outputs: list[EpisodeOutput] = []
        resumed = 0
        total = len(plan.episodes)
        for position, episode in enumerate(plan.episodes):
            if cancel_event and cancel_event.is_set():
                raise PipelineCancelled("Talking-head series generation cancelled.")
            filename = (
                f"episode-{episode.number:03d}-{_slug(episode.title)}.mp4"
            )
            output = request.output_directory / filename
            old = previous_items.get(episode.number, {})
            if old.get("output") == filename and self._valid_previous(old, output):
                resumed += 1
            else:
                def episode_progress(value: float, message: str) -> None:
                    if progress:
                        progress(
                            ((position + value / 100.0) / total) * 100.0,
                            f"Episode {episode.number}/{total}: {message}",
                        )

                result = self.episode_pipeline.run(
                    PodcastRequest(
                        script=episode.text,
                        portrait=request.portrait,
                        reference_audio=request.reference_audio,
                        reference_text=request.reference_text,
                        output=output,
                        work_directory=(
                            request.work_directory
                            / f"episode-{episode.number:03d}"
                        ),
                        target_minutes=max(1.0, episode.estimated_seconds / 60.0),
                        segment_seconds=request.segment_seconds,
                    ),
                    progress=episode_progress,
                    cancel_event=cancel_event,
                )
                output = Path(result.output)
            record = EpisodeOutput(
                episode.number,
                episode.title,
                output.name,
                episode.estimated_seconds,
                self._source_ids(episode),
                _sha256(output),
            )
            outputs.append(record)
            self._atomic_json(
                manifest,
                {
                    "version": 1,
                    "kind": "complete-book-talking-head-series",
                    "fingerprint": fingerprint,
                    "episode_target_minutes": request.episode_minutes,
                    "words_per_minute": request.words_per_minute,
                    "source_order": list(plan.source_order),
                    "source_hashes": dict(plan.source_hashes),
                    "rights_confirmed": True,
                    "episodes": [asdict(item) for item in outputs],
                    "status": "in_progress" if len(outputs) < total else "complete",
                },
            )
            if progress:
                progress(
                    ((position + 1) / total) * 100.0,
                    f"Completed episode {episode.number} of {total}",
                )

        playlist.write_text(
            "#EXTM3U\n"
            + "".join(
                f"#EXTINF:{item.estimated_seconds:.3f},{item.title}\n{item.output}\n"
                for item in outputs
            ),
            encoding="utf-8",
        )
        return SeriesResult(
            str(request.output_directory.resolve()),
            str(manifest.resolve()),
            str(playlist.resolve()),
            tuple(outputs),
            resumed,
        )
