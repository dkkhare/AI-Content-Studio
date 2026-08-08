from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from backend.supporting import REDACTED, SupportBundleService, redact, redact_text


class RedactionTests(unittest.TestCase):
    def test_nested_sensitive_keys_and_text_credentials_are_redacted(self):
        value = {
            "api_key": "top-secret",
            "profile": {
                "Authorization": "Bearer token-value",
                "message": "password=hunter2 token=abcdef",
            },
        }
        result = redact(value)
        self.assertEqual(result["api_key"], REDACTED)
        self.assertEqual(result["profile"]["Authorization"], REDACTED)
        self.assertNotIn("hunter2", result["profile"]["message"])
        self.assertNotIn("abcdef", result["profile"]["message"])

    def test_home_paths_and_provider_tokens_are_redacted(self):
        text = "/home/dev/project sk-abcdefghijklmnop"
        result = redact_text(text, home="/home/dev")
        self.assertIn("%USER_HOME%/project", result)
        self.assertNotIn("sk-abcdefghijklmnop", result)


class SupportBundleTests(unittest.TestCase):
    def test_bundle_is_redacted_manifested_and_checksum_verifiable(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            log = root / "application.log"
            user_home = str(Path.home().resolve())
            log.write_text(
                f"Started {user_home}/project\napi_key=secret-value\n",
                encoding="utf-8",
            )
            service = SupportBundleService(
                allowed_roots=(root,),
                diagnostics_provider=lambda: {
                    "platform": "Windows",
                    "home": user_home,
                    "access_token": "diagnostic-secret",
                },
            )
            output, manifest = service.create(
                root / "support.zip",
                log_paths=(log,),
                settings={
                    "theme": "dark",
                    "provider_secret": "settings-secret",
                },
            )
            self.assertTrue(output.is_file())
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(
                    set(archive.namelist()),
                    {
                        "diagnostics.json",
                        "settings.json",
                        "logs/01-application.log",
                        "manifest.json",
                    },
                )
                combined = b"".join(
                    archive.read(name) for name in archive.namelist()
                ).decode("utf-8")
                for secret in (
                    "secret-value",
                    "diagnostic-secret",
                    "settings-secret",
                    user_home,
                ):
                    self.assertNotIn(secret, combined)
                stored = json.loads(archive.read("manifest.json"))
                self.assertEqual(stored, manifest)
                for asset in stored["assets"]:
                    data = archive.read(asset["name"])
                    self.assertEqual(len(data), asset["size"])
                    self.assertEqual(
                        hashlib.sha256(data).hexdigest(),
                        asset["sha256"],
                    )

    def test_unapproved_unsupported_and_excess_logs_are_rejected(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as outside:
            root = Path(root)
            external = Path(outside) / "outside.log"
            external.write_text("log", encoding="utf-8")
            binary = root / "dump.bin"
            binary.write_bytes(b"binary")
            service = SupportBundleService(allowed_roots=(root,), max_logs=1)
            with self.assertRaisesRegex(ValueError, "approved"):
                service.create(root / "external.zip", log_paths=(external,))
            with self.assertRaisesRegex(ValueError, "Unsupported"):
                service.create(root / "binary.zip", log_paths=(binary,))
            first = root / "first.log"
            second = root / "second.log"
            first.write_text("one", encoding="utf-8")
            second.write_text("two", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "too many"):
                service.create(
                    root / "many.zip",
                    log_paths=(first, second),
                )

    def test_nonoverwrite_limits_and_failure_cleanup(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            destination = root / "support.zip"
            destination.write_bytes(b"keep")
            service = SupportBundleService(allowed_roots=(root,))
            with self.assertRaises(FileExistsError):
                service.create(destination)
            self.assertEqual(destination.read_bytes(), b"keep")

            limited = SupportBundleService(
                allowed_roots=(root,),
                diagnostics_provider=lambda: {"message": "x" * 100},
                max_total_bytes=20,
            )
            failed = root / "failed.zip"
            with self.assertRaisesRegex(ValueError, "total size"):
                limited.create(failed)
            self.assertFalse(failed.exists())
            self.assertEqual(list(root.glob(".failed.zip.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
