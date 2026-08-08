from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReleaseWorkflowSafetyTests(unittest.TestCase):
    def test_release_is_tag_only_and_uses_scoped_write_permission(self):
        workflow = (ROOT / ".github" / "workflows" / "windows-release.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn('tags:\n      - "v*"', workflow)
        self.assertNotIn("pull_request:", workflow)
        self.assertIn("contents: write", workflow)
        self.assertIn("release_version.py --tag", workflow)
        self.assertIn("gh release create", workflow)
        self.assertIn("--verify-tag", workflow)
        self.assertIn("SHA256SUMS.txt", workflow)

    def test_installer_requires_injected_version_and_stable_upgrade_id(self):
        installer = (ROOT / "packaging" / "AIContentStudio.iss").read_text(
            encoding="utf-8"
        )
        self.assertIn("#ifndef MyAppVersion", installer)
        self.assertIn("#error MyAppVersion must be supplied", installer)
        self.assertIn(
            "AppId={{F4C00B07-7F6D-49A7-AE14-7B79D25EAA67}",
            installer,
        )
        self.assertIn("OutputBaseFilename=AIContentStudio-Setup-{#MyAppVersion}", installer)

    def test_executable_metadata_is_derived_from_python_version(self):
        spec = (ROOT / "AIContentStudio.spec").read_text(encoding="utf-8")
        self.assertIn(
            "from backend.version import APP_NAME, VERSION, VERSION_TUPLE",
            spec,
        )
        self.assertIn("filevers={VERSION_TUPLE!r}", spec)
        self.assertIn("ProductVersion', u'{VERSION}'", spec)
        self.assertNotIn("packaging/windows_version_info.txt", spec)


if __name__ == "__main__":
    unittest.main()
