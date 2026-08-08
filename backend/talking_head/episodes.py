from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _digest(value: str) -> str:
    return hashlib.sha256(_clean(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class SourceBlock:
    """Ordered book content with its logical heading preserved."""

    block_id: str
    title: str
    text: str
    level: int = 1

    def __post_init__(self):
        if not self.block_id.strip():
            raise ValueError("Source block ID is required.")
        if not self.text.strip():
            raise ValueError(f"Source block {self.block_id!r} has no text.")
        if self.level < 1:
            raise ValueError("Heading level must be positive.")


@dataclass(frozen=True, slots=True)
class EpisodeFragment:
    source_id: str
    source_title: str
    part: int
    parts: int
    text: str
    estimated_seconds: float

    @property
    def continuation(self) -> bool:
        return self.part > 1


@dataclass(frozen=True, slots=True)
class Episode:
    number: int
    title: str
    fragments: tuple[EpisodeFragment, ...]
    estimated_seconds: float

    @property
    def text(self) -> str:
        return "\n\n".join(item.text for item in self.fragments)


@dataclass(frozen=True, slots=True)
class SeriesPlan:
    episodes: tuple[Episode, ...]
    target_seconds: float
    words_per_minute: float
    source_hashes: tuple[tuple[str, str], ...]
    source_order: tuple[str, ...]

    def validate_coverage(self) -> None:
        planned: dict[str, list[EpisodeFragment]] = {}
        encountered: list[str] = []
        for episode in self.episodes:
            for fragment in episode.fragments:
                if fragment.source_id not in planned:
                    encountered.append(fragment.source_id)
                planned.setdefault(fragment.source_id, []).append(fragment)
        if tuple(encountered) != self.source_order:
            raise ValueError("Episode plan changes the source-block order.")
        expected = dict(self.source_hashes)
        if set(planned) != set(expected):
            missing = sorted(set(expected) - set(planned))
            extra = sorted(set(planned) - set(expected))
            raise ValueError(f"Episode coverage mismatch; missing={missing}, extra={extra}.")
        for source_id, fragments in planned.items():
            parts = [item.part for item in fragments]
            expected_parts = list(range(1, fragments[0].parts + 1))
            if parts != expected_parts or any(item.parts != len(fragments) for item in fragments):
                raise ValueError(f"Duplicate, missing, or unordered parts for {source_id}.")
            if _digest(" ".join(item.text for item in fragments)) != expected[source_id]:
                raise ValueError(f"Episode text does not fully cover source block {source_id}.")


def _sentence_units(text: str) -> list[str]:
    cleaned = _clean(text)
    values = re.split(r"(?<=[.!?।॥])\s+", cleaned)
    return [item for item in values if item]


def _seconds(text: str, words_per_minute: float) -> float:
    words = len(_clean(text).split())
    return words * 60.0 / words_per_minute


def _split_block(
    block: SourceBlock, *, max_seconds: float, words_per_minute: float
) -> list[str]:
    if _seconds(block.text, words_per_minute) <= max_seconds:
        return [_clean(block.text)]
    limit_words = max(1, int(max_seconds * words_per_minute / 60.0))
    parts: list[str] = []
    current: list[str] = []
    count = 0
    for sentence in _sentence_units(block.text):
        words = sentence.split()
        if len(words) > limit_words:
            if current:
                parts.append(" ".join(current))
                current, count = [], 0
            for start in range(0, len(words), limit_words):
                parts.append(" ".join(words[start : start + limit_words]))
            continue
        if current and count + len(words) > limit_words:
            parts.append(" ".join(current))
            current, count = [], 0
        current.append(sentence)
        count += len(words)
    if current:
        parts.append(" ".join(current))
    return parts


def _episode_title(number: int, fragments: list[EpisodeFragment]) -> str:
    first = fragments[0]
    base = first.source_title.strip() or f"Episode {number}"
    if first.continuation:
        return f"{base} — Part {first.part}"
    distinct = []
    for item in fragments:
        title = item.source_title.strip()
        if title and title not in distinct:
            distinct.append(title)
    if len(distinct) == 2:
        return f"{distinct[0]} / {distinct[1]}"
    return base


def plan_episodes(
    blocks: list[SourceBlock] | tuple[SourceBlock, ...],
    *,
    target_minutes: float = 15.0,
    words_per_minute: float = 140.0,
    minimum_ratio: float = 0.72,
    maximum_ratio: float = 1.18,
) -> SeriesPlan:
    """Plan complete-book episodes while favoring logical source boundaries."""
    if not blocks:
        raise ValueError("At least one source block is required.")
    if not 5 <= target_minutes <= 60:
        raise ValueError("Episode target must be between 5 and 60 minutes.")
    if not 60 <= words_per_minute <= 300:
        raise ValueError("Narration speed must be between 60 and 300 words per minute.")
    ids = [item.block_id for item in blocks]
    if len(ids) != len(set(ids)):
        raise ValueError("Source block IDs must be unique.")

    target = target_minutes * 60.0
    minimum = target * minimum_ratio
    maximum = target * maximum_ratio
    fragments: list[EpisodeFragment] = []
    for block in blocks:
        values = _split_block(
            block, max_seconds=maximum, words_per_minute=words_per_minute
        )
        for index, value in enumerate(values, 1):
            fragments.append(
                EpisodeFragment(
                    block.block_id,
                    block.title,
                    index,
                    len(values),
                    value,
                    _seconds(value, words_per_minute),
                )
            )

    episodes: list[Episode] = []
    current: list[EpisodeFragment] = []
    duration = 0.0

    def close_episode() -> None:
        nonlocal current, duration
        if not current:
            return
        number = len(episodes) + 1
        episodes.append(
            Episode(number, _episode_title(number, current), tuple(current), duration)
        )
        current, duration = [], 0.0

    for fragment in fragments:
        new_source = bool(current and fragment.source_id != current[-1].source_id)
        would_exceed = duration + fragment.estimated_seconds > maximum
        near_target_boundary = new_source and duration >= minimum
        if current and (would_exceed or near_target_boundary):
            close_episode()
        current.append(fragment)
        duration += fragment.estimated_seconds
        if duration >= target and fragment.part == fragment.parts:
            close_episode()
    close_episode()

    plan = SeriesPlan(
        tuple(episodes),
        target,
        words_per_minute,
        tuple((item.block_id, _digest(item.text)) for item in blocks),
        tuple(ids),
    )
    plan.validate_coverage()
    return plan
