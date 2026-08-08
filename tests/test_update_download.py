from __future__ import annotations

import hashlib
import io
import tempfile
import unittest
from pathlib import Path
from threading import Event

from backend.updating import (
    InstallerDownloader,
    SemanticVersion,
    UpdateCancelled,
    UpdateRelease,
    parse_checksum_manifest,
)


class Response(io.BytesIO):
    def __init__(self, data, *, content_length=None):
        super().__init__(data)
        self.headers = {}
        if content_length is not None:
            self.headers["Content-Length"] = str(content_length)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def update_release(version="0.20.0"):
    return UpdateRelease(
        version=SemanticVersion.parse(version),
        tag=f"v{version}",
        name=f"Release {version}",
        notes="Changes",
        page_url="https://github.com/releases/latest",
        installer_url="https://github.com/download/installer.exe",
        checksums_url="https://github.com/download/SHA256SUMS.txt",
    )


class ChecksumManifestTests(unittest.TestCase):
    def test_exact_filename_is_required(self):
        digest = "a" * 64
        text = (
            f"{'b' * 64}  directory/AIContentStudio-Setup-0.20.0-windows-x64.exe\n"
            f"{digest} *AIContentStudio-Setup-0.20.0-windows-x64.exe\n"
        )
        self.assertEqual(
            parse_checksum_manifest(
                text, "AIContentStudio-Setup-0.20.0-windows-x64.exe"
            ),
            digest,
        )

    def test_missing_and_duplicate_entries_are_rejected(self):
        filename = "installer.exe"
        with self.assertRaises(ValueError):
            parse_checksum_manifest("not a checksum", filename)
        line = f"{'a' * 64}  {filename}\n"
        with self.assertRaises(ValueError):
            parse_checksum_manifest(line + line, filename)


class InstallerDownloaderTests(unittest.TestCase):
    def downloader(self, installer, checksum=None, **options):
        filename = "AIContentStudio-Setup-0.20.0-windows-x64.exe"
        digest = checksum or hashlib.sha256(installer).hexdigest()
        manifest = f"{digest}  {filename}\n".encode()

        def open_url(url, headers, timeout):
            if url.endswith("SHA256SUMS.txt"):
                return Response(manifest)
            return Response(installer, content_length=len(installer))

        return InstallerDownloader(open_url=open_url, **options)

    def test_verified_download_publishes_atomically_with_progress(self):
        installer = b"verified-installer"
        with tempfile.TemporaryDirectory() as root:
            values = []
            output = self.downloader(installer).download(
                update_release(), root, progress=lambda written, total: values.append((written, total))
            )
            self.assertEqual(output.read_bytes(), installer)
            self.assertEqual(values[-1], (len(installer), len(installer)))
            self.assertEqual(list(Path(root).glob("*.part")), [])
            with self.assertRaises(FileExistsError):
                self.downloader(installer).download(update_release(), root)

    def test_checksum_failure_removes_partial_file(self):
        with tempfile.TemporaryDirectory() as root:
            downloader = self.downloader(b"corrupt", checksum="0" * 64)
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                downloader.download(update_release(), root)
            self.assertEqual(list(Path(root).iterdir()), [])

    def test_size_limit_rejects_download_and_cleans_up(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(ValueError, "size limit"):
                self.downloader(
                    b"too-large", max_installer_bytes=3
                ).download(update_release(), root)
            self.assertEqual(list(Path(root).iterdir()), [])

    def test_cancellation_removes_partial_file(self):
        installer = b"x" * (2 * 1024 * 1024)
        cancelled = Event()

        def progress(written, total):
            cancelled.set()

        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(UpdateCancelled):
                self.downloader(installer).download(
                    update_release(),
                    root,
                    cancel_event=cancelled,
                    progress=progress,
                )
            self.assertEqual(list(Path(root).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
