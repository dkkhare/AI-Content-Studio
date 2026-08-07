from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from backend.knowledge import KnowledgeStore
from backend.production import EpisodeProductionService, EpisodeSubtitleService, EpisodeThumbnailService
from backend.project.project import Project


class FakeFFmpegRunner:
    def __init__(self):
        self.commands = []

    def __call__(self, command, **kwargs):
        self.commands.append(list(command))
        output = Path(command[-1])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"video")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")


class EpisodeProductionTests(unittest.TestCase):
    def test_subtitles_follow_approved_scene_durations(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = KnowledgeStore(root)
            store.initialize()
            store.write("scenes", [
                {"id": "s1", "episode_id": "episode_001", "sequence": 1, "approved": True, "narration": "पहला दृश्य", "duration_seconds": 5},
                {"id": "s2", "episode_id": "episode_001", "sequence": 2, "approved": True, "narration": "दूसरा दृश्य", "duration_seconds": 7.5},
                {"id": "s3", "episode_id": "episode_001", "sequence": 3, "approved": False, "narration": "नहीं आना चाहिए", "duration_seconds": 9},
            ])
            output = EpisodeSubtitleService(root).generate("episode_001")
            text = output.read_text(encoding="utf-8")
            self.assertIn("00:00:00,000 --> 00:00:05,000", text)
            self.assertIn("00:00:05,000 --> 00:00:12,500", text)
            self.assertIn("पहला दृश्य", text)
            self.assertIn("दूसरा दृश्य", text)
            self.assertNotIn("नहीं आना चाहिए", text)

    def test_thumbnail_falls_back_to_first_approved_scene_image(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "segments" / "episode_001" / "images" / "s1.png"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"png")
            store = KnowledgeStore(root)
            store.initialize()
            store.write("assets", [{
                "id": "img1",
                "asset_type": "scene_image",
                "episode_id": "episode_001",
                "owner_id": "s1",
                "path": str(source.relative_to(root)),
                "approved": True,
                "status": "approved",
            }])
            output = EpisodeThumbnailService(root).prepare("episode_001")
            self.assertIsNotNone(output)
            self.assertTrue(output.exists())
            self.assertEqual(output.read_bytes(), b"png")

    def test_export_creates_youtube_ready_asset(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Project("Demo", Path(temp)).initialize()
            project.set_setting("ffmpeg_path", "ffmpeg")
            project.set_setting("production_subtitles_enabled", True)
            project.set_setting("production_burn_subtitles", True)
            project.set_setting("pipeline_episode_production_enabled", True)

            episode_video = project.root / "segments" / "episode_001" / "video" / "episode.mp4"
            episode_video.parent.mkdir(parents=True)
            episode_video.write_bytes(b"episode")

            scene_image = project.root / "segments" / "episode_001" / "images" / "s1.png"
            scene_image.parent.mkdir(parents=True)
            scene_image.write_bytes(b"image")

            store = KnowledgeStore(project.root)
            store.initialize()
            store.write("scenes", [{
                "id": "s1",
                "episode_id": "episode_001",
                "sequence": 1,
                "approved": True,
                "narration": "नमस्ते दुनिया",
                "duration_seconds": 4,
            }])
            store.write("assets", [{
                "id": "img1",
                "asset_type": "scene_image",
                "episode_id": "episode_001",
                "owner_id": "s1",
                "path": str(scene_image.relative_to(project.root)),
                "approved": True,
                "status": "approved",
            }])

            runner = FakeFFmpegRunner()
            service = EpisodeProductionService(project, runner=runner)
            service.available = lambda: True
            output = service.export_episode("episode_001")
            self.assertTrue(output.exists())
            command = runner.commands[-1]
            self.assertIn("+faststart", command)
            self.assertIn("libx264", command)
            self.assertTrue(any("subtitles=" in value for value in command))
            assets = store.read("assets")
            self.assertTrue(any(item.get("asset_type") == "youtube_export" for item in assets))


if __name__ == "__main__":
    unittest.main()
