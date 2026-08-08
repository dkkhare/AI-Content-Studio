from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from backend.publishing import ReleaseManager


class ReleaseManagerTests(unittest.TestCase):
    def _seed_episode(self, root: Path, *, with_video: bool = True, with_thumbnail: bool = True) -> None:
        episode = root / "segments" / "episode_001"
        publish = episode / "publish"
        export = episode / "export"
        publish.mkdir(parents=True)
        export.mkdir(parents=True)
        (episode / "script.txt").write_text("यह हिंदी एपिसोड है।", encoding="utf-8")
        (root / "segments" / "episodes.json").write_text(
            json.dumps({
                "episodes": [{
                    "episode_id": "episode_001",
                    "title": "पहला अध्याय",
                    "text_file": "segments/episode_001/script.txt",
                    "approved": True,
                    "status": "approved",
                }]
            }, ensure_ascii=False),
            encoding="utf-8",
        )
        if with_video:
            (export / "youtube.mp4").write_bytes(b"video")
        if with_thumbnail:
            (export / "thumbnail.png").write_bytes(b"png")
        manifest = {
            "episode_id": "episode_001",
            "youtube": {"title": "पहला अध्याय"},
            "files": {
                "video": "segments/episode_001/export/youtube.mp4",
                "thumbnail": "segments/episode_001/export/thumbnail.png",
            },
            "ready": with_video,
        }
        (publish / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
        )

    def test_ready_requires_manifest_video_and_thumbnail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed_episode(root, with_video=True, with_thumbnail=False)
            manager = ReleaseManager(root)
            check = manager.validation("episode_001")
            self.assertFalse(check["ready"])
            self.assertIn("thumbnail_missing", check["errors"])
            with self.assertRaises(ValueError):
                manager.mark_ready("episode_001")

    def test_draft_ready_published_flow_persists_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed_episode(root)
            manager = ReleaseManager(root)
            self.assertEqual(manager.get("episode_001")["state"], "draft")
            ready = manager.mark_ready("episode_001", note="review complete")
            self.assertEqual(ready["state"], "ready")
            published = manager.mark_published(
                "episode_001",
                destination="YouTube",
                external_id="abc123",
                external_url="https://example.invalid/watch/abc123",
            )
            self.assertEqual(published["state"], "published")
            self.assertEqual(published["destination"], "YouTube")
            self.assertEqual(published["external_id"], "abc123")
            self.assertEqual(len(published["history"]), 2)
            self.assertEqual(published["history"][0]["to"], "ready")
            self.assertEqual(published["history"][1]["to"], "published")
            saved = root / "segments" / "episode_001" / "publish" / "release.json"
            self.assertTrue(saved.exists())

    def test_published_requires_ready_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed_episode(root)
            manager = ReleaseManager(root)
            with self.assertRaises(ValueError):
                manager.mark_published("episode_001", destination="YouTube")

    def test_failed_release_can_return_to_ready_after_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed_episode(root)
            manager = ReleaseManager(root)
            manager.mark_failed("episode_001", "network unavailable")
            self.assertEqual(manager.get("episode_001")["state"], "failed")
            ready = manager.mark_ready("episode_001")
            self.assertEqual(ready["state"], "ready")
            self.assertEqual(ready["error"], "")

    def test_summary_counts_release_states(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed_episode(root)
            manager = ReleaseManager(root)
            manager.mark_ready("episode_001")
            summary = manager.summary()
            self.assertEqual(summary["total"], 1)
            self.assertEqual(summary["ready"], 1)
            self.assertEqual(summary["draft"], 0)


if __name__ == "__main__":
    unittest.main()
