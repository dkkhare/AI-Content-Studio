from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SubtitleCue:
    index: int
    start_ms: int
    end_ms: int
    text: str

    def __post_init__(self):
        if self.index < 1:
            raise ValueError("Subtitle cue index must be positive.")
        if self.start_ms < 0 or self.end_ms <= self.start_ms:
            raise ValueError("Subtitle cue timing must have a positive duration.")
        if not self.text.strip():
            raise ValueError("Subtitle cue text cannot be empty.")


def format_timestamp(milliseconds: int, *, vtt: bool = False) -> str:
    value = max(0, int(milliseconds))
    hours, value = divmod(value, 3_600_000)
    minutes, value = divmod(value, 60_000)
    seconds, millis = divmod(value, 1000)
    separator = "." if vtt else ","
    return f"{hours:02}:{minutes:02}:{seconds:02}{separator}{millis:03}"


class SubtitleDocument:
    def __init__(self, cues):
        self.cues = list(cues)
        previous_end = -1
        for expected, cue in enumerate(self.cues, 1):
            if cue.index != expected:
                raise ValueError("Subtitle cue indexes must be contiguous.")
            if cue.start_ms < previous_end:
                raise ValueError("Subtitle cues cannot overlap.")
            previous_end = cue.end_ms

    def to_srt(self) -> str:
        blocks = []
        for cue in self.cues:
            blocks.append(
                f"{cue.index}\n"
                f"{format_timestamp(cue.start_ms)} --> {format_timestamp(cue.end_ms)}\n"
                f"{cue.text.strip()}"
            )
        return "\n\n".join(blocks) + ("\n" if blocks else "")

    def to_vtt(self) -> str:
        blocks = ["WEBVTT"]
        for cue in self.cues:
            blocks.append(
                f"{format_timestamp(cue.start_ms, vtt=True)} --> "
                f"{format_timestamp(cue.end_ms, vtt=True)}\n{cue.text.strip()}"
            )
        return "\n\n".join(blocks) + "\n"

    def write(self, path, *, format=None) -> Path:
        target = Path(path)
        kind = (format or target.suffix.lstrip(".")).lower()
        if kind not in {"srt", "vtt"}:
            raise ValueError("Subtitle format must be srt or vtt.")
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(
            self.to_srt() if kind == "srt" else self.to_vtt(),
            encoding="utf-8",
        )
        temporary.replace(target)
        return target


class SubtitleGenerator:
    SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?।॥])\s+")

    def __init__(self, *, max_chars=84, words_per_minute=150, gap_ms=80):
        self.max_chars = max(10, int(max_chars))
        self.words_per_minute = max(30, int(words_per_minute))
        self.gap_ms = max(0, int(gap_ms))

    def split_text(self, text):
        value = re.sub(r"\s+", " ", str(text or "")).strip()
        if not value:
            return []
        chunks = []
        for sentence in self.SENTENCE_BOUNDARY.split(value):
            words = sentence.split()
            current = []
            for word in words:
                candidate = " ".join(current + [word])
                if current and len(candidate) > self.max_chars:
                    chunks.append(" ".join(current))
                    current = [word]
                else:
                    current.append(word)
            if current:
                candidate = " ".join(current)
                if chunks and len(chunks[-1]) + 1 + len(candidate) <= self.max_chars:
                    chunks[-1] += " " + candidate
                else:
                    chunks.append(candidate)
        return chunks

    def generate(self, text, *, total_duration_seconds=None):
        chunks = self.split_text(text)
        if not chunks:
            return SubtitleDocument([])

        weights = [max(1, len(chunk.split())) for chunk in chunks]
        gaps_total = self.gap_ms * max(0, len(chunks) - 1)
        if total_duration_seconds is None:
            durations = [
                max(1000, min(7000, round(words * 60_000 / self.words_per_minute)))
                for words in weights
            ]
        else:
            total_ms = round(float(total_duration_seconds) * 1000)
            available = total_ms - gaps_total
            if available < len(chunks) * 250:
                raise ValueError("Audio duration is too short for the subtitle cues.")
            weight_total = sum(weights)
            durations = [round(available * weight / weight_total) for weight in weights]
            durations[-1] += available - sum(durations)

        cues = []
        cursor = 0
        for index, (chunk, duration) in enumerate(zip(chunks, durations), 1):
            end = cursor + duration
            cues.append(SubtitleCue(index, cursor, end, chunk))
            cursor = end + self.gap_ms
        return SubtitleDocument(cues)
