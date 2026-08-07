from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import re
from pathlib import Path


_HEADING_RE = re.compile(
    r"^(?:अध्याय|अध्याय\s+\d+|खंड|भाग|प्रकरण|परिच्छेद|chapter|part|section)\b",
    re.IGNORECASE,
)


@dataclass
class EpisodeSegment:
    episode_id: str
    title: str
    text: str
    word_count: int
    estimated_minutes: float
    source_start_paragraph: int
    source_end_paragraph: int
    status: str = "planned"
    approved: bool = False
    text_file: str = ""

    def to_dict(self) -> dict:
        data = asdict(self)
        data.pop("text", None)
        return data


class SegmentPlanner:
    """Split long Hindi narration into logical ~15 minute episode units."""

    def __init__(
        self,
        *,
        target_minutes: float = 15.0,
        min_minutes: float = 12.0,
        max_minutes: float = 18.0,
        words_per_minute: float = 130.0,
    ):
        self.target_minutes = max(1.0, float(target_minutes))
        self.min_minutes = max(1.0, float(min_minutes))
        self.max_minutes = max(self.min_minutes, float(max_minutes))
        self.words_per_minute = max(1.0, float(words_per_minute))

    @staticmethod
    def _paragraphs(text: str) -> list[str]:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        return [part.strip() for part in re.split(r"\n\s*\n+", normalized) if part.strip()]

    @staticmethod
    def _word_count(text: str) -> int:
        return len(re.findall(r"\S+", text, flags=re.UNICODE))

    @staticmethod
    def _is_heading(paragraph: str) -> bool:
        first_line = paragraph.splitlines()[0].strip()
        if _HEADING_RE.match(first_line):
            return True
        return len(first_line) <= 80 and first_line.endswith((":", "—"))

    def _minutes_for_words(self, words: int) -> float:
        return words / self.words_per_minute

    def plan(self, text: str) -> list[EpisodeSegment]:
        paragraphs = self._paragraphs(text)
        if not paragraphs:
            return []

        target_words = self.target_minutes * self.words_per_minute
        min_words = self.min_minutes * self.words_per_minute
        max_words = self.max_minutes * self.words_per_minute

        groups: list[tuple[int, int, list[str]]] = []
        current: list[str] = []
        current_words = 0
        start_index = 0

        for index, paragraph in enumerate(paragraphs):
            words = self._word_count(paragraph)
            heading = self._is_heading(paragraph)

            # Prefer chapter/section endings once a useful episode length has been reached.
            if heading and current and current_words >= min_words:
                groups.append((start_index, index - 1, current))
                current = []
                current_words = 0
                start_index = index

            # If adding this paragraph would exceed the hard upper bound, close at the
            # previous paragraph boundary. This never cuts a sentence or paragraph.
            if current and current_words + words > max_words:
                groups.append((start_index, index - 1, current))
                current = []
                current_words = 0
                start_index = index

            current.append(paragraph)
            current_words += words

            # Once near the target, a strong paragraph ending is an acceptable cut.
            if current_words >= target_words and paragraph.rstrip().endswith(("।", "॥", ".", "!", "?")):
                groups.append((start_index, index, current))
                current = []
                current_words = 0
                start_index = index + 1

        if current:
            groups.append((start_index, len(paragraphs) - 1, current))

        # Avoid a tiny final episode when it can safely be merged into the previous one.
        if len(groups) >= 2:
            last_words = sum(self._word_count(p) for p in groups[-1][2])
            previous_words = sum(self._word_count(p) for p in groups[-2][2])
            if last_words < min_words and previous_words + last_words <= max_words:
                previous = groups[-2]
                last = groups[-1]
                groups[-2] = (previous[0], last[1], previous[2] + last[2])
                groups.pop()

        episodes: list[EpisodeSegment] = []
        for number, (start, end, parts) in enumerate(groups, start=1):
            episode_text = "\n\n".join(parts).strip()
            words = self._word_count(episode_text)
            first_line = parts[0].splitlines()[0].strip() if parts else ""
            if self._is_heading(parts[0]) and first_line:
                title = first_line
            else:
                title = f"Episode {number:03d}"
            episodes.append(
                EpisodeSegment(
                    episode_id=f"episode_{number:03d}",
                    title=title,
                    text=episode_text,
                    word_count=words,
                    estimated_minutes=round(self._minutes_for_words(words), 2),
                    source_start_paragraph=start,
                    source_end_paragraph=end,
                )
            )
        return episodes

    def persist(self, project_root: str | Path, episodes: list[EpisodeSegment]) -> Path:
        root = Path(project_root).resolve()
        segments_root = root / "segments"
        segments_root.mkdir(parents=True, exist_ok=True)

        for episode in episodes:
            episode_dir = segments_root / episode.episode_id
            episode_dir.mkdir(parents=True, exist_ok=True)
            text_file = episode_dir / "script.txt"
            text_file.write_text(episode.text, encoding="utf-8")
            episode.text_file = str(text_file.relative_to(root))

        manifest = segments_root / "episodes.json"
        payload = {
            "target_minutes": self.target_minutes,
            "min_minutes": self.min_minutes,
            "max_minutes": self.max_minutes,
            "words_per_minute": self.words_per_minute,
            "episodes": [episode.to_dict() for episode in episodes],
        }
        manifest.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return manifest
