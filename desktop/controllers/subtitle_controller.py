from __future__ import annotations

from pathlib import Path

from backend.subtitles import (
    ProjectSubtitleService,
    SubtitleCue,
    SubtitleDocument,
    parse_timestamp,
    read_subtitles,
)


class SubtitleDesktopController:
    """Project-aware facade for subtitle generation, editing and export."""

    def __init__(self, service=None):
        self.service = service or ProjectSubtitleService()
        self.project = None
        self.document = SubtitleDocument([])

    def set_project(self, project):
        self.project = project
        self.document = SubtitleDocument([])
        raw = getattr(project, "subtitle_file", "") if project is not None else ""
        if raw:
            path = Path(raw)
            if not path.is_absolute():
                path = Path(project.root) / path
            if path.is_file():
                self.document = read_subtitles(path)
        return self.document

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
