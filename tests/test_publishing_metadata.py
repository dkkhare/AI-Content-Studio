from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from backend.knowledge import KnowledgeStore
from backend.project.project import Project
from backend.publishing import PublishingMetadataService


class PublishingMetadataTests(unittest.TestCase):
    def _project(self, root: Path) -> Project:
        project = Project(name="Hindi Book", root=root, author="लेखक")
        project.settings.update({
            "publishing_channel_name": "सरस्वती कथा",
            "publishing_title_prefix": "कहानी:",
            "publishing_default_keywords": "भारतीय कथा, ज्ञान",
            "publishing_description_intro": "इस हिंदी एपिसोड में आपका स्वागत है।",
        })
        return project

    def _seed(self, root: Path) -> None:
        episode_dir = root / "segments" / "episode_001"
        episode_dir.mkdir(parents=True)
        (episode_dir / "script.txt").write_text("राम वन की ओर जाते हैं और सीता से संवाद करते हैं।", encoding="utf-8")
        (root / "segments" / "episodes.json").write_text(json.dumps({
            "episodes": [{
                "episode_id": "episode_001",
                "title": "वन यात्रा",
                "episode_number": 1,
                "text_file": "segments/episode_001/script.txt",
                "approved": True,
                "status": "approved",
            }, {
                "episode_id": "episode_002",
                "title": "अस्वीकृत",
                "text_file": "segments/episode_002/script.txt",
                "approved": False,
                "status": "planned",
            }]
        }, ensure_ascii=False), encoding="utf-8")
        store = KnowledgeStore(root)
        store.initialize()
        store.write("scenes", [
            {"id": "scene_a", "episode_id": "episode_001", "sequence": 1, "approved": True, "summary": "वन में प्रवेश", "duration_seconds": 30},
            {"id": "scene_b", "episode_id": "episode_001", "sequence": 2, "approved": True, "summary": "सीता से संवाद", "duration_seconds": 45},
            {"id": "scene_c", "episode_id": "episode_001", "sequence": 3, "approved": False, "summary": "नहीं", "duration_seconds": 20},
        ])
        store.write("characters", [{"id": "char_ram", "name": "राम", "approved": True, "episode_ids": ["episode_001"]}])
        store.write("locations", [{"id": "loc_forest", "name": "वन", "approved": True, "episode_ids": ["episode_001"]}])
        export = root / "segments" / "episode_001" / "export"
        export.mkdir(parents=True)
        (export / "youtube.mp4").write_bytes(b"video")
        (export / "thumbnail.png").write_bytes(b"png")
        store.upsert("assets", {"id": "youtube_episode_001", "asset_type": "youtube_export", "episode_id": "episode_001", "owner_id": "episode_001", "path": "segments/episode_001/export/youtube.mp4"})
        store.upsert("assets", {"id": "thumb_episode_001", "asset_type": "episode_thumbnail", "episode_id": "episode_001", "owner_id": "episode_001", "path": "segments/episode_001/export/thumbnail.png"})

    def test_build_manifest_has_hindi_metadata_chapters_and_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed(root)
            service = PublishingMetadataService(self._project(root))
            manifest = service.build_episode("episode_001")
            self.assertEqual(manifest["language"], "hi")
            self.assertTrue(manifest["youtube"]["title"].startswith("कहानी:"))
            self.assertIn("इस हिंदी एपिसोड", manifest["youtube"]["description"])
            self.assertEqual([c["timestamp"] for c in manifest["youtube"]["chapters"]], ["0:00", "0:30"])
            self.assertIn("राम", manifest["youtube"]["tags"])
            self.assertIn("वन", manifest["youtube"]["tags"])
            self.assertEqual(manifest["podcast"]["language"], "hi-IN")
            self.assertEqual(manifest["files"]["video"], "segments/episode_001/export/youtube.mp4")
            self.assertTrue(manifest["ready"])
            path = root / "segments" / "episode_001" / "publish" / "manifest.json"
            self.assertTrue(path.exists())

    def test_build_all_only_processes_approved_episodes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed(root)
            outputs = PublishingMetadataService(self._project(root)).build_all()
            self.assertEqual(len(outputs), 1)
            self.assertEqual(outputs[0]["episode_id"], "episode_001")
            self.assertFalse((root / "segments" / "episode_002" / "publish" / "manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
