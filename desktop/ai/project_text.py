from __future__ import annotations

from pathlib import Path


class ProjectTextService:
    """Safely discover, load, and save text artifacts for the AI workbench."""

    ALLOWED_SUFFIXES = {".txt", ".md", ".json", ".srt", ".vtt", ".csv"}
    PROJECT_FIELDS = ("ocr_file", "translation_file", "subtitle_file")
    KNOWN_OUTPUTS = (
        "output/ocr_cleaned.txt",
        "output/hindi_spelling_corrected.txt",
        "output/hindi_grammar_corrected.txt",
        "output/script.txt",
    )

    def __init__(self, max_bytes: int = 5 * 1024 * 1024):
        self.max_bytes = max(1, int(max_bytes))

    @staticmethod
    def _path(project, value) -> Path:
        path = Path(str(value))
        if not path.is_absolute():
            path = Path(project.root) / path
        return path.resolve()

    def sources(self, project) -> list[tuple[str, Path]]:
        if project is None:
            return []
        values: list[tuple[str, Path]] = []
        seen: set[Path] = set()
        for field in self.PROJECT_FIELDS:
            raw = getattr(project, field, "")
            if raw:
                path = self._path(project, raw)
                if self._readable(path) and path not in seen:
                    seen.add(path)
                    values.append((field.replace("_", " ").title(), path))
        for relative in self.KNOWN_OUTPUTS:
            path = self._path(project, relative)
            if self._readable(path) and path not in seen:
                seen.add(path)
                values.append((Path(relative).stem.replace("_", " ").title(), path))
        return values

    def _readable(self, path: Path) -> bool:
        return (
            path.is_file()
            and path.suffix.lower() in self.ALLOWED_SUFFIXES
            and path.stat().st_size <= self.max_bytes
        )

    def read(self, path: str | Path) -> str:
        value = Path(path).resolve()
        if not self._readable(value):
            raise ValueError("Selected project artifact is not a supported text file or is too large.")
        return value.read_text(encoding="utf-8", errors="replace")

    def save_output(self, project, text: str) -> Path:
        if project is None:
            raise RuntimeError("Open a project before saving AI output.")
        value = str(text)
        if not value.strip():
            raise ValueError("AI output is empty.")
        target = Path(project.root).resolve() / "output" / "ai_workbench_output.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(".tmp")
        temporary.write_text(value, encoding="utf-8")
        temporary.replace(target)
        project.touch()
        return target
