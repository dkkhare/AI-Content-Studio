from __future__ import annotations

from pathlib import Path

from .core import SubtitleDocument, SubtitleGenerator
from .parser import read_subtitles


class ProjectSubtitleService:
    """Generate, import, and register subtitle artifacts for a project."""

    def __init__(self, generator: SubtitleGenerator | None = None):
        self.generator = generator or SubtitleGenerator()

    @staticmethod
    def _output_root(project) -> Path:
        if project is None or not getattr(project, "root", None):
            raise ValueError("An open project is required.")
        root = Path(project.root).resolve()
        output = (root / str(getattr(project, "output_directory", "output"))).resolve()
        if output != root and root not in output.parents:
            raise ValueError("Project output directory must remain inside the project.")
        output.mkdir(parents=True, exist_ok=True)
        return output

    @staticmethod
    def _register(project, target: Path) -> None:
        if hasattr(project, "add_output_file"):
            project.add_output_file("subtitle_file", str(target))
        else:
            project.subtitle_file = str(target)
            if hasattr(project, "touch"):
                project.touch()

    def generate(
        self,
        project,
        text: str,
        *,
        audio_duration_seconds: float,
        format: str = "srt",
        filename: str | None = None,
    ) -> SubtitleDocument:
        kind = str(format).lower().lstrip(".")
        if kind not in {"srt", "vtt"}:
            raise ValueError("Subtitle format must be srt or vtt.")
        document = self.generator.generate(
            text, total_duration_seconds=audio_duration_seconds
        )
        if not document.cues:
            raise ValueError("Narration text is required to generate subtitles.")
        output = self._output_root(project)
        safe_name = Path(filename or f"subtitles.{kind}").name
        if Path(safe_name).suffix.lower() != f".{kind}":
            raise ValueError("Subtitle filename extension does not match its format.")
        target = document.write(output / safe_name, format=kind).resolve()
        self._register(project, target)
        return document

    def import_file(self, project, source) -> SubtitleDocument:
        source_path = Path(source).resolve()
        document = read_subtitles(source_path)
        output = self._output_root(project)
        target = output / f"subtitles{source_path.suffix.lower()}"
        document.write(target)
        self._register(project, target.resolve())
        return document
