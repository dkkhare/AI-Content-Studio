from __future__ import annotations

import hashlib
import json
import os
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from uuid import uuid4

from backend.runtime import app_data_dir, diagnostics

from .redaction import redact, redact_text


ALLOWED_LOG_SUFFIXES = {".json", ".log", ".txt"}
DEFAULT_MAX_FILE_BYTES = 5 * 1024 * 1024
DEFAULT_MAX_TOTAL_BYTES = 20 * 1024 * 1024
DEFAULT_MAX_LOGS = 10


@dataclass(frozen=True)
class SupportAsset:
    name: str
    size: int
    sha256: str


class SupportBundleService:
    def __init__(
        self,
        *,
        allowed_roots=None,
        diagnostics_provider=None,
        max_file_bytes=DEFAULT_MAX_FILE_BYTES,
        max_total_bytes=DEFAULT_MAX_TOTAL_BYTES,
        max_logs=DEFAULT_MAX_LOGS,
    ):
        roots = allowed_roots or (app_data_dir(),)
        self.allowed_roots = tuple(Path(root).expanduser().resolve() for root in roots)
        self.diagnostics_provider = diagnostics_provider or diagnostics
        self.max_file_bytes = max(1, int(max_file_bytes))
        self.max_total_bytes = max(1, int(max_total_bytes))
        self.max_logs = max(0, int(max_logs))

    def _log_path(self, source):
        path = Path(source).expanduser().resolve()
        suffixes = {suffix.lower() for suffix in path.suffixes}
        if not suffixes.intersection(ALLOWED_LOG_SUFFIXES):
            raise ValueError(f"Unsupported support log type: {path.suffix}")
        if not path.is_file():
            raise FileNotFoundError(path)
        if not any(path == root or root in path.parents for root in self.allowed_roots):
            raise ValueError("Support log must remain inside an approved application directory.")
        if path.stat().st_size > self.max_file_bytes:
            raise ValueError(f"Support log exceeded the per-file size limit: {path.name}")
        return path

    def discover_log_paths(self, directories):
        candidates = []
        for directory in directories:
            directory = Path(directory).expanduser().resolve()
            if not directory.is_dir():
                continue
            for path in directory.iterdir():
                if not path.is_file():
                    continue
                try:
                    approved = self._log_path(path)
                except (FileNotFoundError, ValueError):
                    continue
                candidates.append(approved)
        return tuple(
            sorted(
                candidates,
                key=lambda path: (path.stat().st_mtime_ns, path.name),
                reverse=True,
            )[: self.max_logs]
        )

    @staticmethod
    def _json_bytes(value):
        return (
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")

    def create(self, destination, *, log_paths=(), settings=None):
        destination = Path(destination).expanduser().resolve()
        if destination.suffix.lower() != ".zip":
            raise ValueError("Support bundle destination must use the .zip extension.")
        if destination.exists():
            raise FileExistsError(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.parent / f".{destination.name}.{uuid4().hex}.tmp"

        entries = {}
        total = 0

        def add(name, data):
            nonlocal total
            if len(data) > self.max_file_bytes:
                raise ValueError(f"Support entry exceeded the per-file size limit: {name}")
            total += len(data)
            if total > self.max_total_bytes:
                raise ValueError("Support bundle exceeded the total size limit.")
            entries[name] = data

        try:
            add(
                "diagnostics.json",
                self._json_bytes(redact(self.diagnostics_provider())),
            )
            add(
                "settings.json",
                self._json_bytes(redact(settings or {})),
            )
            paths = list(log_paths)
            if len(paths) > self.max_logs:
                raise ValueError("Support bundle contains too many log files.")
            for index, source in enumerate(paths, start=1):
                path = self._log_path(source)
                text = path.read_text(encoding="utf-8", errors="replace")
                add(
                    f"logs/{index:02d}-{path.name}",
                    (redact_text(text) + ("" if text.endswith("\n") else "\n")).encode(
                        "utf-8"
                    ),
                )

            assets = tuple(
                SupportAsset(
                    name=name,
                    size=len(data),
                    sha256=hashlib.sha256(data).hexdigest(),
                )
                for name, data in sorted(entries.items())
            )
            manifest = {
                "format": 1,
                "privacy": "Sensitive settings, credentials, and user-home paths are redacted.",
                "assets": [asdict(asset) for asset in assets],
            }
            entries["manifest.json"] = self._json_bytes(manifest)

            with zipfile.ZipFile(
                temporary,
                "x",
                compression=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            ) as archive:
                for name, data in sorted(entries.items()):
                    archive.writestr(name, data)
            os.replace(temporary, destination)
            return destination, manifest
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
