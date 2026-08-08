from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend import runtime
from desktop.main import main, parse_args


class RuntimeTests(unittest.TestCase):
    def test_source_runtime_paths_and_local_app_data(self):
        with patch.object(runtime.sys, "frozen", False, create=True):
            self.assertFalse(runtime.is_frozen())
            self.assertTrue(runtime.bundle_root().is_dir())
            self.assertEqual(
                runtime.app_data_dir({"LOCALAPPDATA": "relative-data"}).name,
                runtime.APP_ID,
            )

    def test_frozen_runtime_uses_executable_and_bundle_paths(self):
        with tempfile.TemporaryDirectory() as root:
            executable = Path(root) / "AIContentStudio.exe"
            bundle = Path(root) / "_internal"
            with (
                patch.object(runtime.sys, "frozen", True, create=True),
                patch.object(runtime.sys, "executable", str(executable)),
                patch.object(runtime.sys, "_MEIPASS", str(bundle), create=True),
            ):
                self.assertEqual(runtime.bundle_root(), bundle.resolve())
                self.assertEqual(runtime.executable_dir(), Path(root).resolve())
                self.assertTrue(runtime.diagnostics()["frozen"])

    def test_diagnostics_cli_writes_atomic_json_without_starting_qt(self):
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / "diagnostics.json"
            self.assertEqual(main(["--diagnostics", str(output)]), 0)
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(data["application"], "AI Content Studio")
            self.assertEqual(data["application_id"], "AIContentStudio")
            self.assertEqual(data["version"], "0.19.0")
            self.assertIn("ffmpeg_available", data)
            self.assertTrue(data["resources_available"])
            self.assertTrue(data["resources"]["desktop/themes/dark.qss"])
            self.assertFalse(output.with_suffix(".json.tmp").exists())

    def test_resource_path_rejects_absolute_and_parent_traversal(self):
        with self.assertRaises(ValueError):
            runtime.resource_path("../secret")
        with self.assertRaises(ValueError):
            runtime.resource_path(Path.cwd().anchor + "secret")

    def test_cli_rejects_unknown_arguments(self):
        with self.assertRaises(SystemExit):
            parse_args(["--unknown"])


if __name__ == "__main__":
    unittest.main()
