from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from backend.episodes import SegmentPlanner
from backend.pipeline.context import PipelineContext
from backend.pipeline.episode_stage import EpisodePlanningStage
from backend.project.project import Project


class EpisodeSegmentationTests(unittest.TestCase):
    @staticmethod
    def _paragraph(prefix: str, words: int = 260) -> str:
        return prefix + " " + " ".join(["कहानी"] * max(1, words - 1)) + "।"

    def test_planner_prefers_chapter_boundary_near_target(self):
        planner = SegmentPlanner(
            target_minutes=15,
            min_minutes=12,
            max_minutes=18,
            words_per_minute=100,
        )
        text = "\n\n".join(
            [
                "अध्याय 1",
                *[self._paragraph(f"पहला-{i}") for i in range(6)],
                "अध्याय 2",
                *[self._paragraph(f"दूसरा-{i}") for i in range(5)],
            ]
        )

        episodes = planner.plan(text)
        self.assertGreaterEqual(len(episodes), 2)
        self.assertTrue(episodes[0].title.startswith("अध्याय 1"))
        self.assertTrue(episodes[1].title.startswith("अध्याय 2"))
        self.assertLessEqual(episodes[0].estimated_minutes, 18.0)

    def test_persist_creates_review_manifest_and_episode_scripts(self):
        planner = SegmentPlanner(words_per_minute=100)
        episodes = planner.plan("अध्याय 1\n\n" + self._paragraph("पाठ", 500))

        with tempfile.TemporaryDirectory() as temp:
            manifest = planner.persist(temp, episodes)
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(len(payload["episodes"]), 1)
            record = payload["episodes"][0]
            self.assertEqual(record["status"], "planned")
            self.assertFalse(record["approved"])
            self.assertTrue((Path(temp) / record["text_file"]).exists())

    def test_pipeline_stage_prefers_podcast_script_and_exposes_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Project("Hindi", Path(temp)).initialize()
            context = PipelineContext(project)
            context.ocr_text = "पुराना OCR पाठ"
            context.set("script_text", "अध्याय 1\n\n" + self._paragraph("स्वीकृत स्क्रिप्ट", 500))

            result = EpisodePlanningStage(words_per_minute=100).execute(context)
            self.assertTrue(Path(result).exists())
            self.assertTrue(context.get("episodes"))
            text_file = Path(temp) / context.get("episodes")[0]["text_file"]
            self.assertIn("स्वीकृत स्क्रिप्ट", text_file.read_text(encoding="utf-8"))
            self.assertNotIn("पुराना OCR पाठ", text_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
