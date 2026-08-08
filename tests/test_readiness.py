from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.project.project import Project
from backend.readiness import ReadinessService


class ReadinessTests(unittest.TestCase):
    def test_optional_integrations_do_not_block_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = Project(name="Ready", root=root)
            project.update_settings({
                "ai_provider": "openai",
                "pipeline_narration_enabled": False,
                "pipeline_image_generation_enabled": False,
                "pipeline_video_enabled": False,
                "publishing_provider": "manual",
            })
            with patch("backend.readiness.shutil.which", side_effect=lambda name: "/usr/bin/ffmpeg" if name == "ffmpeg" else None):
                report = ReadinessService(project).run()
            self.assertTrue(report["ready"])
            self.assertEqual(report["blocker_count"], 0)
            self.assertGreaterEqual(report["warning_count"], 1)
            persisted = json.loads((root / "readiness.json").read_text(encoding="utf-8"))
            self.assertTrue(persisted["ready"])

    def test_missing_required_ffmpeg_and_f5tts_are_blockers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = Project(name="Blocked", root=root)
            project.update_settings({
                "ai_provider": "openai",
                "pipeline_narration_enabled": True,
                "tts_provider": "f5tts",
                "pipeline_image_generation_enabled": False,
                "pipeline_video_enabled": False,
                "publishing_provider": "manual",
            })
            with patch("backend.readiness.shutil.which", return_value=None), patch("backend.readiness.importlib.util.find_spec", return_value=None):
                report = ReadinessService(project).run()
            self.assertFalse(report["ready"])
            failed_required = {item["id"] for item in report["checks"] if item["required"] and not item["ok"]}
            self.assertIn("ffmpeg", failed_required)
            self.assertIn("f5tts", failed_required)
            self.assertIn("reference_voice", failed_required)

    def test_enabled_local_image_cli_becomes_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            executable = root / "image-tool"
            executable.write_text("tool", encoding="utf-8")
            project = Project(name="Images", root=root)
            project.update_settings({
                "ai_provider": "openai",
                "pipeline_narration_enabled": False,
                "pipeline_image_generation_enabled": True,
                "image_provider": "local_cli",
                "image_cli_executable": str(executable),
                "image_cli_arguments": "--prompt {prompt}",
                "pipeline_video_enabled": False,
                "publishing_provider": "manual",
            })
            with patch("backend.readiness.shutil.which", side_effect=lambda name: "/usr/bin/ffmpeg" if name == "ffmpeg" else None):
                report = ReadinessService(project).run()
            image = next(item for item in report["checks"] if item["id"] == "image_provider")
            self.assertTrue(image["required"])
            self.assertTrue(image["ok"])


if __name__ == "__main__":
    unittest.main()
