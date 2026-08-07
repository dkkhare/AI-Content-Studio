from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from backend.knowledge import KnowledgeStore
from backend.video import (
    EpisodeVideoAssembler,
    LocalCommandVideoProvider,
    SceneVideoService,
    VideoAssetReviewStore,
    VideoGenerationRequest,
)


class FakeVideoProvider:
    provider_id = "fake-local-video"

    def __init__(self):
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        request.output.parent.mkdir(parents=True, exist_ok=True)
        request.output.write_bytes(b"video")
        return request.output


class LocalVideoGenerationTests(unittest.TestCase):
    def _project(self, root: Path):
        store = KnowledgeStore(root)
        store.initialize()
        store.write(
            "scenes",
            [
                {
                    "id": "scene_001",
                    "episode_id": "episode_001",
                    "sequence": 1,
                    "approved": True,
                    "status": "approved",
                    "duration_seconds": 8.5,
                    "video_prompt": "धीरे कैमरा आगे बढ़े",
                }
            ],
        )
        image = root / "segments" / "episode_001" / "images" / "scene_001.png"
        image.parent.mkdir(parents=True, exist_ok=True)
        image.write_bytes(b"image")
        store.write(
            "assets",
            [
                {
                    "id": "image_1",
                    "asset_type": "scene_image",
                    "owner_id": "scene_001",
                    "episode_id": "episode_001",
                    "path": str(image.relative_to(root)),
                    "approved": True,
                    "status": "approved",
                }
            ],
        )
        return store

    def test_scene_clip_uses_approved_image_prompt_and_duration(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._project(root)
            provider = FakeVideoProvider()
            service = SceneVideoService(root, provider, fps=30, width=1280, height=720)
            assets = service.generate_scene_clips()
            self.assertEqual(len(assets), 1)
            request = provider.requests[0]
            self.assertEqual(request.duration_seconds, 8.5)
            self.assertEqual(request.fps, 30)
            self.assertEqual(request.width, 1280)
            self.assertEqual(request.height, 720)
            self.assertTrue(request.image.exists())
            self.assertIn("धीरे", request.prompt)
            self.assertFalse(assets[0]["approved"])
            self.assertEqual(assets[0]["status"], "pending_review")

    def test_video_review_requires_explicit_approval(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._project(root)
            assets = SceneVideoService(root, FakeVideoProvider()).generate_scene_clips()
            review = VideoAssetReviewStore(root)
            self.assertFalse(review.clip_review_complete())
            review.approve(assets[0]["id"])
            self.assertTrue(review.clip_review_complete())

    def test_local_command_renders_timing_placeholders(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            exe = root / "video-tool.exe"
            exe.write_bytes(b"tool")
            output = root / "out.mp4"
            image = root / "image.png"
            image.write_bytes(b"image")
            calls = []

            def runner(command, **kwargs):
                calls.append(command)
                output.write_bytes(b"video")
                return subprocess.CompletedProcess(command, 0, "", "")

            provider = LocalCommandVideoProvider(
                str(exe),
                '--prompt "{prompt}" --image "{image}" --duration {duration} --fps {fps} --width {width} --height {height} --output "{output}"',
                runner=runner,
            )
            provider.generate(VideoGenerationRequest("motion", output, image, 6.25, 24, 960, 544))
            command = " ".join(calls[0])
            self.assertIn("6.250", command)
            self.assertIn("24", command)
            self.assertIn("960", command)
            self.assertIn("544", command)

    def test_episode_assembler_uses_only_approved_clips_and_narration(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = KnowledgeStore(root)
            store.initialize()
            clip = root / "segments" / "episode_001" / "video" / "clips" / "scene_001.mp4"
            clip.parent.mkdir(parents=True, exist_ok=True)
            clip.write_bytes(b"clip")
            audio = root / "segments" / "episode_001" / "audio" / "narration.wav"
            audio.parent.mkdir(parents=True, exist_ok=True)
            audio.write_bytes(b"audio")
            store.write("assets", [{
                "id": "clip_1", "asset_type": "scene_video", "owner_id": "scene_001",
                "episode_id": "episode_001", "path": str(clip.relative_to(root)),
                "approved": True, "status": "approved",
            }])
            ffmpeg = root / "ffmpeg.exe"
            ffmpeg.write_bytes(b"tool")
            calls = []

            def runner(command, **kwargs):
                calls.append(command)
                Path(command[-1]).write_bytes(b"episode")
                return subprocess.CompletedProcess(command, 0, "", "")

            output = EpisodeVideoAssembler(root, ffmpeg_path=str(ffmpeg), runner=runner).assemble_episode("episode_001")
            self.assertTrue(output.exists())
            self.assertIn(str(audio), calls[0])
            episode_assets = [item for item in store.read("assets") if item.get("asset_type") == "episode_video"]
            self.assertEqual(len(episode_assets), 1)


if __name__ == "__main__":
    unittest.main()
