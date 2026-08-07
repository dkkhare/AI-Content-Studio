from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from backend.knowledge import KnowledgeStore, ProjectStatusService
from backend.project.project import Project


class KnowledgeStoreTests(unittest.TestCase):
    def test_initialize_creates_canonical_files_without_overwriting(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = KnowledgeStore(root)
            store.initialize()
            expected = {
                "book.json",
                "characters.json",
                "locations.json",
                "objects.json",
                "timeline.json",
                "relationships.json",
                "glossary.json",
                "pronunciation.json",
                "style.json",
                "scenes.json",
                "prompts.json",
                "assets.json",
            }
            self.assertEqual(expected, {path.name for path in store.root.glob("*.json")})

            store.write("book", {"title": "कहानी"})
            store.initialize()
            self.assertEqual(store.read("book")["title"], "कहानी")

    def test_upsert_preserves_existing_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            store = KnowledgeStore(temp)
            store.initialize()
            store.upsert("characters", {"id": "char_1", "name": "मोहन", "approved": False})
            result = store.upsert("characters", {"id": "char_1", "approved": True})
            self.assertEqual(result["name"], "मोहन")
            self.assertTrue(result["approved"])
            self.assertEqual(len(store.read("characters")), 1)

    def test_project_status_reads_episode_and_knowledge_state(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Project("Hindi Book", Path(temp)).initialize()
            output = project.output_path()
            (output / "ocr.txt").write_text("पाठ", encoding="utf-8")
            (output / "podcast_script.txt").write_text("स्क्रिप्ट", encoding="utf-8")

            store = KnowledgeStore(project.root)
            store.initialize()
            store.write(
                "characters",
                [
                    {"id": "char_1", "name": "मोहन", "approved": True},
                    {"id": "char_2", "name": "सीता", "approved": False},
                ],
            )
            store.write("locations", [{"id": "loc_1", "name": "गाँव", "approved": False}])
            store.write("scenes", [{"id": "scene_1"}, {"id": "scene_2"}])

            segments = project.root / "segments"
            segments.mkdir(parents=True)
            (segments / "episodes.json").write_text(
                json.dumps(
                    {
                        "episodes": [
                            {"episode_id": "episode_001", "approved": True, "status": "approved"},
                            {"episode_id": "episode_002", "approved": False, "status": "planned"},
                            {"episode_id": "episode_003", "approved": False, "status": "skipped"},
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            audio = segments / "episode_001" / "audio"
            audio.mkdir(parents=True)
            (audio / "narration.wav").write_bytes(b"audio")

            status = ProjectStatusService(project).snapshot()
            self.assertTrue(status["ocr"])
            self.assertTrue(status["script"])
            self.assertEqual(status["episodes_planned"], 3)
            self.assertEqual(status["episodes_approved"], 1)
            self.assertEqual(status["episodes_skipped"], 1)
            self.assertEqual(status["episodes_pending"], 1)
            self.assertEqual(status["character_count"], 2)
            self.assertEqual(status["characters_pending"], 1)
            self.assertEqual(status["locations_pending"], 1)
            self.assertEqual(status["scene_count"], 2)
            self.assertEqual(status["audio_episode_count"], 1)


if __name__ == "__main__":
    unittest.main()
