from __future__ import annotations

import wave
from pathlib import Path

from backend.subtitles import (
    ProjectSubtitleService,
    SubtitleCue,
    SubtitleDocument,
    parse_timestamp,
    read_subtitles,
)


class SubtitleDesktopController:
    """Project-aware facade for subtitle generation, editing and preview."""

    TEXT_FIELDS = ("translation_file", "ocr_file")
    TEXT_OUTPUTS = ("output/script.txt", "output/ai_workbench_output.txt")
    AUDIO_FIELDS = ("narration_file", "audiobook_file", "podcast_file")
    MAX_TEXT_BYTES = 5 * 1024 * 1024

    def __init__(self, service=None):
        self.service = service or ProjectSubtitleService()
        self.project = None
        self.document = SubtitleDocument([])

    def _project_path(self, value):
        path = Path(str(value))
        if not path.is_absolute():
            path = Path(self.project.root) / path
        path = path.resolve()
        root = Path(self.project.root).resolve()
        if path != root and root not in path.parents:
            raise ValueError("Project assets must remain inside the project.")
        return path

    def set_project(self, project):
        self.project = project
        self.document = SubtitleDocument([])
        raw = getattr(project, "subtitle_file", "") if project is not None else ""
        if raw:
            path = self._project_path(raw)
            if path.is_file():
                self.document = read_subtitles(path)
        return self.document

    def narration_audio(self):
        if self.project is None:
            return None
        for field in self.AUDIO_FIELDS:
            raw = getattr(self.project, field, "")
            if raw:
                path = self._project_path(raw)
                if path.is_file():
                    return path
        return None

    def narration_text(self):
        if self.project is None:
            return ""
        candidates = [
            getattr(self.project, field, "") for field in self.TEXT_FIELDS
        ] + list(self.TEXT_OUTPUTS)
        for raw in candidates:
            if not raw:
                continue
            path = self._project_path(raw)
            if (
                path.is_file()
                and path.suffix.lower() in {".txt", ".md"}
                and path.stat().st_size <= self.MAX_TEXT_BYTES
            ):
                return path.read_text(encoding="utf-8", errors="replace").strip()
        return ""

    def audio_duration_seconds(self, path=None):
        source = Path(path).resolve() if path else self.narration_audio()
        if source is None or not source.is_file():
            return 0.0
        if source.suffix.lower() == ".wav":
            with wave.open(str(source), "rb") as audio:
                rate = audio.getframerate()
                return audio.getnframes() / rate if rate else 0.0
        try:
            import soundfile as sf
            info = sf.info(source)
            return info.frames / info.samplerate if info.samplerate else 0.0
        except Exception:
            return 0.0

    def project_context(self):
        audio = self.narration_audio()
        return {
            "text": self.narration_text(),
            "audio_path": str(audio) if audio else "",
            "duration_seconds": self.audio_duration_seconds(audio),
        }

    def generate(self, text, duration_seconds, *, format="srt"):
        if self.project is None:
            raise RuntimeError("Open a project before generating subtitles.")
        self.document = self.service.generate(
            self.project,
            text,
            audio_duration_seconds=float(duration_seconds),
            format=format,
        )
        return self.document

    def import_file(self, path):
        if self.project is None:
            raise RuntimeError("Open a project before importing subtitles.")
        self.document = self.service.import_file(self.project, path)
        return self.document

    def export_file(self, path):
        if not self.document.cues:
            raise ValueError("There are no subtitle cues to export.")
        return self.document.write(path)

    def replace_cues(self, rows):
        cues = []
        for index, row in enumerate(rows, 1):
            start = row["start_ms"] if "start_ms" in row else parse_timestamp(row["start"])
            end = row["end_ms"] if "end_ms" in row else parse_timestamp(row["end"])
            cues.append(SubtitleCue(index, int(start), int(end), str(row["text"])))
        self.document = SubtitleDocument(cues)
        return self.document

    def cue_at(self, position_ms):
        value = max(0, int(position_ms))
        for cue in self.document.cues:
            if cue.start_ms <= value < cue.end_ms:
                return cue
            if cue.start_ms > value:
                break
        return None

    def cue_rows(self):
        return [
            {
                "index": cue.index,
                "start_ms": cue.start_ms,
                "end_ms": cue.end_ms,
                "text": cue.text,
            }
            for cue in self.document.cues
        ]
