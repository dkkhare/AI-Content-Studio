from __future__ import annotations

from pathlib import Path

from .core import VideoComposer


class ProjectVideoService:
    """Build and persist a safe, renderer-independent project composition plan."""

    def __init__(self, composer=None):
        self.composer = composer or VideoComposer()

    @staticmethod
    def _inside_project(project, value: str | Path) -> Path:
        root = Path(project.root).resolve()
        path = Path(value)
        if not path.is_absolute():
            path = root / path
        path = path.resolve()
        if path != root and root not in path.parents:
            raise ValueError("Video assets must remain inside the project.")
        return path

    def create_manifest(
        self,
        project,
        *,
        visual,
        audio,
        duration_seconds,
        subtitles=None,
        width=1920,
        height=1080,
        fps=30,
        output="output/video_manifest.json",
    ):
        manifest = self.composer.plan(
            visual=self._inside_project(project, visual),
            audio=self._inside_project(project, audio),
            subtitles=(
                self._inside_project(project, subtitles)
                if subtitles is not None
                else None
            ),
            duration_seconds=duration_seconds,
            width=width,
            height=height,
            fps=fps,
        )
        target = self._inside_project(project, output)
        if target.suffix.lower() != ".json":
            raise ValueError("Composition manifest output must be a JSON file.")
        manifest.write(target)
        return manifest, target
