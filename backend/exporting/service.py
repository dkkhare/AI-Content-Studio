from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

from .core import PRESETS, ExportAsset, ExportManifest, ExportPreset


class ExportCancelled(RuntimeError):
    pass


class ProjectExportService:
    """Publish verified project assets as an atomic directory package."""

    def __init__(self, presets=None, copy_file=shutil.copy2):
        self.presets = dict(presets or PRESETS)
        self.copy_file = copy_file

    @staticmethod
    def _project_asset(project, value):
        root = Path(project.root).resolve()
        path = Path(str(value))
        if not path.is_absolute():
            path = root / path
        path = path.resolve()
        if path != root and root not in path.parents:
            raise ValueError("Export assets must remain inside the project.")
        return path

    def preset(self, value: str | ExportPreset):
        if isinstance(value, ExportPreset):
            return value
        try:
            return self.presets[str(value)]
        except KeyError as exc:
            raise ValueError(f"Unknown export preset: {value}") from exc

    def collect(self, project, preset="publishing"):
        selected = self.preset(preset)
        sources = []
        missing = []
        for role in selected.assets:
            raw = getattr(project, role, "")
            if not raw:
                if role in selected.required:
                    missing.append(role)
                continue
            source = self._project_asset(project, raw)
            if not source.is_file():
                if role in selected.required:
                    missing.append(role)
                continue
            sources.append((role, source))
        if missing:
            raise ValueError("Missing required export assets: " + ", ".join(missing))
        if not sources:
            raise ValueError("No project assets are available for export.")
        return selected, sources

    @staticmethod
    def _filename(role, source, used):
        candidate = source.name
        if candidate.casefold() in used:
            candidate = f"{role}-{source.name}"
        index = 2
        stem, suffix = Path(candidate).stem, Path(candidate).suffix
        while candidate.casefold() in used:
            candidate = f"{stem}-{index}{suffix}"
            index += 1
        used.add(candidate.casefold())
        return candidate

    def export(
        self,
        project,
        destination,
        preset="publishing",
        *,
        progress=None,
        cancel_event=None,
    ):
        selected, sources = self.collect(project, preset)
        target = Path(destination).resolve()
        if target.exists():
            raise FileExistsError(f"Export destination already exists: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        stage = Path(
            tempfile.mkdtemp(prefix=f".{target.name}-", suffix=".tmp", dir=target.parent)
        )
        assets = []
        used = {"manifest.json"}
        try:
            if progress is not None:
                progress(0.0)
            total = len(sources)
            for index, (role, source) in enumerate(sources, 1):
                if cancel_event is not None and cancel_event.is_set():
                    raise ExportCancelled("Project export was cancelled.")
                filename = self._filename(role, source, used)
                copied = stage / filename
                self.copy_file(source, copied)
                assets.append(ExportAsset.from_file(role, copied, filename))
                if progress is not None:
                    progress(index * 95.0 / total)
            if cancel_event is not None and cancel_event.is_set():
                raise ExportCancelled("Project export was cancelled.")
            manifest = ExportManifest(project.name, selected.name, tuple(assets))
            manifest.write(stage / "manifest.json")
            os.replace(stage, target)
            if progress is not None:
                progress(100.0)
            return manifest, target
        except BaseException:
            shutil.rmtree(stage, ignore_errors=True)
            raise
