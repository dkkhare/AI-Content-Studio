from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from backend.project.project import Project
from backend.publishing import PublishResult, PublishingProvider, PublishingService, ReleaseManager, YouTubePublishingProvider


class FakeProvider(PublishingProvider):
    provider_id = "fake"
    display_name = "Fake"

    def __init__(self, *, fail: bool = False):
        self.fail = fail
        self.calls = []

    def publish(self, manifest, *, root):
        self.calls.append((manifest, root))
        if self.fail:
            raise RuntimeError("upload exploded")
        return PublishResult(
            external_id="abc123",
            external_url="https://example.test/abc123",
            destination="fake",
        )


class PublishingProviderTests(unittest.TestCase):
    def _seed_ready(self, root: Path) -> Project:
        episode_dir = root / "segments" / "episode_001"
        publish_dir = episode_dir / "publish"
        export_dir = episode_dir / "export"
        publish_dir.mkdir(parents=True)
        export_dir.mkdir(parents=True)
        (episode_dir / "script.txt").write_text("हिंदी कहानी", encoding="utf-8")
        (root / "segments" / "episodes.json").write_text(json.dumps({
            "episodes": [{
                "episode_id": "episode_001",
                "title": "पहला भाग",
                "text_file": "segments/episode_001/script.txt",
                "approved": True,
                "status": "approved",
            }]
        }, ensure_ascii=False), encoding="utf-8")
        (export_dir / "youtube.mp4").write_bytes(b"video")
        (export_dir / "thumbnail.png").write_bytes(b"png")
        manifest = {
            "episode_id": "episode_001",
            "youtube": {
                "title": "हिंदी कहानी",
                "description": "विवरण",
                "tags": ["हिंदी", "कहानी"],
                "privacy": "private",
                "category_id": "27",
            },
            "files": {
                "video": "segments/episode_001/export/youtube.mp4",
                "thumbnail": "segments/episode_001/export/thumbnail.png",
            },
        }
        (publish_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        project = Project(name="Book", root=root)
        ReleaseManager(root).mark_ready("episode_001")
        return project

    def test_successful_provider_marks_release_published(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = self._seed_ready(root)
            provider = FakeProvider()
            service = PublishingService(project, providers={"fake": provider})
            release = service.publish_episode("episode_001", "fake")
            self.assertEqual(release["state"], "published")
            self.assertEqual(release["external_id"], "abc123")
            self.assertEqual(release["external_url"], "https://example.test/abc123")
            self.assertEqual(len(provider.calls), 1)

    def test_provider_failure_marks_release_failed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = self._seed_ready(root)
            service = PublishingService(project, providers={"fake": FakeProvider(fail=True)})
            with self.assertRaisesRegex(RuntimeError, "upload exploded"):
                service.publish_episode("episode_001", "fake")
            release = ReleaseManager(root).get("episode_001")
            self.assertEqual(release["state"], "failed")
            self.assertIn("upload exploded", release["error"])

    def test_non_ready_episode_cannot_publish(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = self._seed_ready(root)
            ReleaseManager(root).mark_draft("episode_001")
            service = PublishingService(project, providers={"fake": FakeProvider()})
            with self.assertRaisesRegex(ValueError, "must be Ready"):
                service.publish_episode("episode_001", "fake")

    def test_youtube_body_uses_hindi_manifest_metadata(self):
        manifest = {
            "youtube": {
                "title": "मेरी हिंदी कहानी",
                "description": "विवरण",
                "tags": ["हिंदी", "कथा"],
                "privacy": "unlisted",
                "category_id": "27",
                "made_for_kids": False,
            }
        }
        body = YouTubePublishingProvider._body(manifest)
        self.assertEqual(body["snippet"]["title"], "मेरी हिंदी कहानी")
        self.assertEqual(body["snippet"]["defaultLanguage"], "hi")
        self.assertEqual(body["status"]["privacyStatus"], "unlisted")
        self.assertEqual(body["snippet"]["categoryId"], "27")


if __name__ == "__main__":
    unittest.main()
