from __future__ import annotations

import json
import os
import platform
import shutil
import sys
from pathlib import Path

from backend.version import APP_ID, APP_NAME, VERSION


REQUIRED_RESOURCES = ("desktop/themes/dark.qss",)


def is_frozen():
    return bool(getattr(sys, "frozen", False))


def bundle_root():
    if is_frozen() and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS).resolve()
    return Path(__file__).resolve().parents[1]


def resource_path(relative_path):
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Resource path must be relative and contained.")
    return bundle_root() / relative


def validate_resources(resources=REQUIRED_RESOURCES):
    return {
        item: resource_path(item).is_file()
        for item in resources
    }


def executable_dir():
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return bundle_root()


def app_data_dir(env=None):
    values = os.environ if env is None else env
    base = values.get("LOCALAPPDATA") or values.get("XDG_DATA_HOME")
    if base:
        return Path(base).expanduser().resolve() / APP_ID
    return Path.home().resolve() / f".{APP_ID.lower()}"


def diagnostics(env=None):
    data_dir = app_data_dir(env)
    ffmpeg = shutil.which("ffmpeg")
    resources = validate_resources()
    return {
        "application": APP_NAME,
        "application_id": APP_ID,
        "version": VERSION,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "frozen": is_frozen(),
        "bundle_root": str(bundle_root()),
        "executable_dir": str(executable_dir()),
        "app_data_dir": str(data_dir),
        "app_data_parent_exists": data_dir.parent.is_dir(),
        "ffmpeg": str(Path(ffmpeg).resolve()) if ffmpeg else "",
        "ffmpeg_available": bool(ffmpeg),
        "resources": resources,
        "resources_available": all(resources.values()),
    }


def write_diagnostics(path, env=None):
    destination = Path(path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(
        json.dumps(diagnostics(env), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(destination)
    return destination
