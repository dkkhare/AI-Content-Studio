from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from backend.project.project import Project
from backend.publishing import PublishResult, PublishingProvider, PublishingService, ReleaseManager, YouTubePublishingProvider


class RecordingProvider(PublishingProvider):
    provider_id = "recording"
    display_name = "Recording"

    def __init__(self):
        self.calls = []

    def publish(self, manifest, *, root):
        self.calls.append(manifest)
        episode_id = str(manifest.get("episode_id", ""))
        return PublishResult(external_id=episode_id, external_url=f"https://example.test/{episode_id}", destination="recording")


class PublishingScheduleTests(unittest.TestCase):
    def _seed(self, root: Path) -> Project:
        episodes = []
        for number in (2, 1):
            episode_id = f"episode_{number:03d}"
            folder = root / "segments" / episode_id
            publish = folder / "publish"
            export = folder / "export"
            publish.mkdir(parents=True)
            export.mkdir(parents=True)
            (folder / "script.txt").write_text("हिंदी कथा", encoding="utf-8")
            (export / "youtube.mp4").write_bytes(b"video")
            (export / "thumbnail.png").write_bytes(b"png")
            (publish / "manifest.json").write_text(json.dumps({
                "episode_id": episode_id,
                "youtube": {"title": episode_id, "privacy": "public"},
                "files": {
                    "video": f"segments/{episode_id}/export/youtube.mp4",
                    "thumbnail": f"segments/{episode_id}/export/thumbnail.png",
                },
            }), encoding="utf-8")
            episodes.append({
                "episode_id": episode_id,
                "episode_number": number,
                "title": episode_id,
                "text_file": f"segments/{episode_id}/script.txt",
                "approved": True,
                "status": "approved",
            })
        (root / "segments" / "episodes.json").write_text(json.dumps({"episodes": episodes}), encoding="utf-8")
        manager = ReleaseManager(root)
        manager.mark_ready("episode_001")
        manager.mark_ready("episode_002")
        return Project(name="Book", root=root)

    def test_schedule_normalizes_timezone_and_persists_playlist(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed(root)
            record = ReleaseManager(root).configure_distribution(
                "episode_001",
                publish_at="2026-08-10T18:00:00+05:30",
                playlist_id="PL123",
            )
            self.assertEqual(record["scheduled_publish_at"], "2026-08-10T12:30:00Z")
            self.assertEqual(record["playlist_id"], "PL123")

    def test_youtube_body_for_schedule_forces_private_and_publish_at(self):
        body = YouTubePublishingProvider._body({"youtube": {
            "title": "भाग 1",
            "privacy": "public",
            "publish_at": "2026-08-10T12:30:00Z",
        }})
        self.assertEqual(body["status"]["privacyStatus"], "private")
        self.assertEqual(body["status"]["publishAt"], "2026-08-10T12:30:00Z")

    def test_bulk_publish_preserves_episode_order_and_injects_distribution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = self._seed(root)
            manager = ReleaseManager(root)
            manager.configure_distribution("episode_001", publish_at="2026-08-10T18:00:00+05:30", playlist_id="PLBOOK")
            provider = RecordingProvider()
            results = PublishingService(project, providers={"recording": provider}).publish_ready("recording")
            self.assertEqual([item["episode_id"] for item in results], ["episode_001", "episode_002"])
            self.assertEqual([item["episode_id"] for item in provider.calls], ["episode_001", "episode_002"])
            self.assertEqual(provider.calls[0]["youtube"]["publish_at"], "2026-08-10T12:30:00Z")
            self.assertEqual(provider.calls[0]["youtube"]["playlist_id"], "PLBOOK")


if __name__ == "__main__":
    unittest.main()
