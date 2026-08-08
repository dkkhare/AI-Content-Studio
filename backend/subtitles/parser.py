from __future__ import annotations

import re
from pathlib import Path

from .core import SubtitleCue, SubtitleDocument


_TIMESTAMP = re.compile(
    r"^(?P<hours>\d{2,}):(?P<minutes>[0-5]\d):"
    r"(?P<seconds>[0-5]\d)[,.](?P<millis>\d{3})$"
)


def parse_timestamp(value: str) -> int:
    match = _TIMESTAMP.fullmatch(str(value).strip())
    if not match:
        raise ValueError(f"Invalid subtitle timestamp: {value}")
    return (
        int(match["hours"]) * 3_600_000
        + int(match["minutes"]) * 60_000
        + int(match["seconds"]) * 1000
        + int(match["millis"])
    )


def _timing(line: str) -> tuple[int, int]:
    if "-->" not in line:
        raise ValueError("Subtitle cue is missing a timing separator.")
    start, end = (part.strip() for part in line.split("-->", 1))
    # WebVTT permits cue settings after the end timestamp.
    end = end.split()[0] if end else end
    return parse_timestamp(start), parse_timestamp(end)


def parse_srt(text: str) -> SubtitleDocument:
    value = str(text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not value:
        return SubtitleDocument([])
    cues = []
    for expected, block in enumerate(re.split(r"\n\s*\n", value), 1):
        lines = block.splitlines()
        if len(lines) < 3:
            raise ValueError(f"Invalid SRT cue {expected}.")
        try:
            source_index = int(lines[0].strip())
        except ValueError as exc:
            raise ValueError(f"Invalid SRT cue index at cue {expected}.") from exc
        if source_index != expected:
            raise ValueError("SRT cue indexes must be contiguous.")
        start, end = _timing(lines[1])
        cues.append(SubtitleCue(expected, start, end, "\n".join(lines[2:]).strip()))
    return SubtitleDocument(cues)


def parse_vtt(text: str) -> SubtitleDocument:
    value = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = value.splitlines()
    if not lines or lines[0].lstrip("\ufeff").strip() != "WEBVTT":
        raise ValueError("WebVTT document must begin with WEBVTT.")
    body = "\n".join(lines[1:]).strip()
    if not body:
        return SubtitleDocument([])

    cues = []
    for block in re.split(r"\n\s*\n", body):
        cue_lines = block.splitlines()
        if cue_lines[0].startswith(("NOTE", "STYLE", "REGION")):
            continue
        timing_index = next(
            (index for index, line in enumerate(cue_lines[:2]) if "-->" in line),
            None,
        )
        if timing_index is None or timing_index + 1 >= len(cue_lines):
            raise ValueError(f"Invalid WebVTT cue {len(cues) + 1}.")
        start, end = _timing(cue_lines[timing_index])
        text_lines = cue_lines[timing_index + 1 :]
        cues.append(SubtitleCue(len(cues) + 1, start, end, "\n".join(text_lines).strip()))
    return SubtitleDocument(cues)


def parse_subtitles(text: str, format: str) -> SubtitleDocument:
    kind = str(format).strip().lower().lstrip(".")
    if kind == "srt":
        return parse_srt(text)
    if kind == "vtt":
        return parse_vtt(text)
    raise ValueError("Subtitle format must be srt or vtt.")


def read_subtitles(path) -> SubtitleDocument:
    source = Path(path)
    if source.suffix.lower() not in {".srt", ".vtt"}:
        raise ValueError("Subtitle file must use .srt or .vtt.")
    return parse_subtitles(source.read_text(encoding="utf-8-sig"), source.suffix)
