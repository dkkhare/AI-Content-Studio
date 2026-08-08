from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.release_version import read_version, validate_tag


class ReleaseVersionTests(unittest.TestCase):
    def test_reads_semantic_version_without_importing_module(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "version.py"
            path.write_text('VERSION = "1.2.3"\n', encoding="utf-8")
            self.assertEqual(read_version(path), "1.2.3")

    def test_rejects_missing_dynamic_and_invalid_versions(self):
        values = (
            "APP_NAME = 'test'\n",
            "VERSION = get_version()\n",
            "VERSION = '1.2'\n",
            "VERSION = '01.2.3'\n",
        )
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "version.py"
            for value in values:
                path.write_text(value, encoding="utf-8")
                with self.assertRaises(ValueError):
                    read_version(path)

    def test_release_tag_must_exactly_match_version(self):
        self.assertEqual(validate_tag("v0.19.0", "0.19.0"), "v0.19.0")
        for tag in ("0.19.0", "v0.19.1", "latest"):
            with self.assertRaises(ValueError):
                validate_tag(tag, "0.19.0")


if __name__ == "__main__":
    unittest.main()
