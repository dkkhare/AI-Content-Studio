from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from urllib.request import Request, urlopen
from uuid import uuid4


CHECKSUM_LINE = re.compile(r"^([0-9a-fA-F]{64})\s+[ *]?(.+?)\s*$")
MAX_CHECKSUM_BYTES = 1024 * 1024
DEFAULT_MAX_INSTALLER_BYTES = 1024 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024


class UpdateCancelled(RuntimeError):
    pass


def parse_checksum_manifest(text, expected_filename):
    matches = []
    for line in str(text).splitlines():
        match = CHECKSUM_LINE.fullmatch(line)
        if not match:
            continue
        filename = match.group(2).replace("\\", "/")
        if filename == expected_filename:
            matches.append(match.group(1).lower())
    if not matches:
        raise ValueError(f"Checksum not found for {expected_filename}.")
    if len(matches) != 1:
        raise ValueError(f"Checksum manifest contains duplicate entries for {expected_filename}.")
    return matches[0]


def _open_url(url, headers, timeout):
    return urlopen(Request(url, headers=headers), timeout=timeout)


class InstallerDownloader:
    def __init__(
        self,
        *,
        open_url=None,
        timeout=30,
        max_installer_bytes=DEFAULT_MAX_INSTALLER_BYTES,
    ):
        self.open_url = open_url or _open_url
        self.timeout = max(1, min(int(timeout), 120))
        self.max_installer_bytes = max(1, int(max_installer_bytes))
        self.headers = {
            "Accept": "application/octet-stream",
            "User-Agent": "AIContentStudio-Updater",
        }

    def _read_checksum(self, release):
        with self.open_url(
            release.checksums_url, self.headers, self.timeout
        ) as response:
            data = response.read(MAX_CHECKSUM_BYTES + 1)
        if len(data) > MAX_CHECKSUM_BYTES:
            raise ValueError("Checksum manifest exceeded the safety limit.")
        filename = f"AIContentStudio-Setup-{release.version}-windows-x64.exe"
        return filename, parse_checksum_manifest(data.decode("utf-8-sig"), filename)

    @staticmethod
    def _cancelled(cancel_event):
        return cancel_event is not None and cancel_event.is_set()

    def download(self, release, directory, *, cancel_event=None, progress=None):
        filename, expected_sha256 = self._read_checksum(release)
        directory = Path(directory).expanduser().resolve()
        directory.mkdir(parents=True, exist_ok=True)
        destination = directory / filename
        if destination.exists():
            raise FileExistsError(f"Installer destination already exists: {destination}")
        temporary = directory / f".{filename}.{uuid4().hex}.part"
        digest = hashlib.sha256()
        written = 0
        try:
            if self._cancelled(cancel_event):
                raise UpdateCancelled("Update download cancelled.")
            with self.open_url(
                release.installer_url, self.headers, self.timeout
            ) as response:
                raw_length = response.headers.get("Content-Length")
                total = int(raw_length) if raw_length and raw_length.isdigit() else 0
                if total > self.max_installer_bytes:
                    raise ValueError("Installer exceeded the configured size limit.")
                with temporary.open("xb") as stream:
                    while True:
                        if self._cancelled(cancel_event):
                            raise UpdateCancelled("Update download cancelled.")
                        chunk = response.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        written += len(chunk)
                        if written > self.max_installer_bytes:
                            raise ValueError("Installer exceeded the configured size limit.")
                        stream.write(chunk)
                        digest.update(chunk)
                        if progress is not None:
                            progress(written, total)
                    stream.flush()
                    os.fsync(stream.fileno())
            if written == 0:
                raise ValueError("Downloaded installer was empty.")
            if digest.hexdigest().lower() != expected_sha256:
                raise ValueError("Installer SHA-256 verification failed.")
            os.replace(temporary, destination)
            return destination
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
