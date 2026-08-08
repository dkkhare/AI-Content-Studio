from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from backend.exporting import ExportPreset, ProjectExportService
from backend.project.project import Project


class ExportPresetTests(unittest.TestCase):
    def test_invalid_presets_are_rejected(self):
        for args in (("", ("video_file",)), ("empty", ()), ("dup", ("video_file", "video_file"))):
            with self.assertRaises(ValueError):
                ExportPreset(*args)
        with self.assertRaises(ValueError):
            ExportPreset("bad", ("video_file",), ("subtitle_file",))


class ProjectExportServiceTests(unittest.TestCase):
    def _project(self, root):
        root = Path(root)
        project = Project("प्रकाशन", root).initialize()
        video = root / "output" / "video.mp4"
        subtitle = root / "output" / "subtitles.srt"
        cover = root / "cover.png"
        video.write_bytes(b"video-data")
        subtitle.write_text("नमस्ते", encoding="utf-8")
        cover.write_bytes(b"cover-data")
        project.video_file = str(video)
        project.subtitle_file = str(subtitle)
        project.cover_image = str(cover)
        return project

    def test_publishing_export_has_checksums_and_unicode_manifest(self):
        with tempfile.TemporaryDirectory() as root:
            project = self._project(root)
            destination = Path(root) / "published"
            manifest, output = ProjectExportService().export(
                project, destination, "publishing"
            )
            self.assertEqual(output, destination.resolve())
            self.assertEqual(manifest.project, "प्रकाशन")
            self.assertEqual(manifest.preset, "publishing")
            data = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(data["project"], "प्रकाशन")
            self.assertEqual(len(data["assets"]), 3)
            for asset in data["assets"]:
                self.assertEqual(len(asset["sha256"]), 64)
                self.assertEqual((output / asset["filename"]).stat().st_size, asset["size"])

    def test_required_missing_and_unknown_preset_are_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            project = Project("Empty", Path(root)).initialize()
            service = ProjectExportService()
            with self.assertRaisesRegex(ValueError, "video_file"):
                service.collect(project, "video")
            with self.assertRaisesRegex(ValueError, "Unknown"):
                service.collect(project, "missing")

    def test_assets_outside_project_are_rejected(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as outside:
            project = Project("Unsafe", Path(root)).initialize()
            external = Path(outside) / "video.mp4"
            external.write_bytes(b"video")
            project.video_file = str(external)
            with self.assertRaisesRegex(ValueError, "inside the project"):
                ProjectExportService().collect(project, "video")

    def test_existing_destination_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as root:
            project = self._project(root)
            destination = Path(root) / "published"
            destination.mkdir()
            marker = destination / "keep.txt"
            marker.write_text("keep", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                ProjectExportService().export(project, destination)
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    def test_collision_safe_names_and_failed_copy_cleanup(self):
        with tempfile.TemporaryDirectory() as root:
            project = self._project(root)
            second = Path(root) / "other" / "video.mp4"
            second.parent.mkdir()
            second.write_bytes(b"audio")
            project.narration_file = str(second)
            preset = ExportPreset(
                "collision", ("video_file", "narration_file"), ("video_file",)
            )
            service = ProjectExportService({"collision": preset})
            manifest, output = service.export(
                project, Path(root) / "collision", "collision"
            )
            names = [asset.filename for asset in manifest.assets]
            self.assertEqual(len(names), len(set(names)))
            self.assertIn("narration_file-video.mp4", names)

            calls = 0

            def fail_second(source, destination):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("copy failed")
                destination.write_bytes(Path(source).read_bytes())

            failing = ProjectExportService({"collision": preset}, copy_file=fail_second)
            target = Path(root) / "failed"
            with self.assertRaisesRegex(OSError, "copy failed"):
                failing.export(project, target, "collision")
            self.assertFalse(target.exists())
            self.assertEqual(list(Path(root).glob(".failed-*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
