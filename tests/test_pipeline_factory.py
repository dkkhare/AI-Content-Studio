from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.ai import AIResponse
from backend.episodes import EpisodeReviewStore, SegmentPlanner
from backend.knowledge import KnowledgeStore
from backend.pipeline import build_project_pipeline
from backend.project.project import Project
from backend.scenes import SceneReviewStore


class FakeTranslator:
    def configured(self):
        return True

    def translate(self, text, **kwargs):
        return f"translated:{text}"


class FakeRenderer:
    def render(self, context, progress=None):
        output = context.project.output_path() / "fake.mp4"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"video")
        return output


class FakeAIManager:
    def execute_prompt(self, name, variables=None, **kwargs):
        return AIResponse(text=f"{name}:{(variables or {}).get('text', '')}", provider="fake")


class PipelineFactoryTests(unittest.TestCase):
    def test_default_project_stops_at_episode_planning_for_review(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Project("Demo", Path(temp)).initialize()
            pipeline = build_project_pipeline(project, ai_manager=FakeAIManager())
            self.assertEqual(project.language, "hi")
            self.assertEqual(project.get_setting("ai_provider"), "ollama")
            self.assertEqual(project.get_setting("tts_provider"), "f5tts")
            self.assertTrue(project.get_setting("episode_review_required"))
            self.assertTrue(project.get_setting("pipeline_story_intelligence_enabled"))
            self.assertFalse(project.get_setting("pipeline_hindi_spelling_correction_enabled"))
            self.assertFalse(project.get_setting("pipeline_hindi_grammar_correction_enabled"))
            self.assertEqual([stage.stage_id for stage in pipeline.stages], ["ocr", "ai_script", "episode_planning"])

    def test_spelling_and_grammar_are_independently_optional(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Project("Demo", Path(temp)).initialize()
            project.set_setting("pipeline_hindi_spelling_correction_enabled", True)
            project.set_setting("pipeline_hindi_grammar_correction_enabled", True)
            pipeline = build_project_pipeline(project, ai_manager=FakeAIManager())
            self.assertEqual(
                [stage.stage_id for stage in pipeline.stages],
                ["ocr", "hindi_spelling_correction", "hindi_grammar_correction", "ai_script", "episode_planning"],
            )
            project.set_setting("pipeline_hindi_spelling_correction_enabled", False)
            pipeline = build_project_pipeline(project, ai_manager=FakeAIManager())
            self.assertIn("hindi_grammar_correction", [stage.stage_id for stage in pipeline.stages])
            self.assertNotIn("hindi_spelling_correction", [stage.stage_id for stage in pipeline.stages])

    def test_pending_episode_review_blocks_media_and_story_analysis(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Project("Demo", Path(temp)).initialize()
            planner = SegmentPlanner(target_minutes=1, min_minutes=1, max_minutes=2, words_per_minute=20)
            planner.persist(project.root, planner.plan("अध्याय 1\n\n" + "शब्द " * 25))
            pipeline = build_project_pipeline(project, ai_manager=FakeAIManager())
            stage_ids = [stage.stage_id for stage in pipeline.stages]
            self.assertNotIn("story_intelligence", stage_ids)
            self.assertNotIn("scene_director", stage_ids)
            self.assertNotIn("episode_narration", stage_ids)
            self.assertNotIn("episode_planning", stage_ids)

    def test_completed_episode_and_story_review_runs_scene_director_before_media(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Project("Demo", Path(temp)).initialize()
            planner = SegmentPlanner(target_minutes=1, min_minutes=1, max_minutes=2, words_per_minute=20)
            planner.persist(project.root, planner.plan("अध्याय 1\n\n" + "शब्द " * 25))
            store = EpisodeReviewStore(project.root)
            for episode in store.episodes():
                store.approve(str(episode["episode_id"]))
            pipeline = build_project_pipeline(project, ai_manager=FakeAIManager())
            stage_ids = [stage.stage_id for stage in pipeline.stages]
            self.assertIn("story_intelligence", stage_ids)
            self.assertIn("scene_director", stage_ids)
            self.assertNotIn("episode_narration", stage_ids)
            self.assertLess(stage_ids.index("story_intelligence"), stage_ids.index("scene_director"))

    def test_completed_scene_review_enables_episode_narration(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Project("Demo", Path(temp)).initialize()
            planner = SegmentPlanner(target_minutes=1, min_minutes=1, max_minutes=2, words_per_minute=20)
            planner.persist(project.root, planner.plan("अध्याय 1\n\n" + "शब्द " * 25))
            episodes = EpisodeReviewStore(project.root)
            for episode in episodes.episodes():
                episodes.approve(str(episode["episode_id"]))
            episode_id = str(episodes.approved()[0]["episode_id"])
            knowledge = KnowledgeStore(project.root)
            knowledge.initialize()
            knowledge.write("scenes", [{"id": "scene_1", "episode_id": episode_id, "sequence": 1, "approved": False, "status": "planned"}])
            SceneReviewStore(project.root).approve("scene_1")
            pipeline = build_project_pipeline(project, ai_manager=FakeAIManager())
            stage_ids = [stage.stage_id for stage in pipeline.stages]
            self.assertIn("story_intelligence", stage_ids)
            self.assertNotIn("scene_director", stage_ids)
            self.assertIn("episode_narration", stage_ids)

    def test_hindi_to_hindi_translation_is_skipped(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Project("Demo", Path(temp)).initialize()
            project.set_setting("pipeline_translation_enabled", True)
            pipeline = build_project_pipeline(project, ai_manager=FakeAIManager())
            self.assertNotIn("translation", [stage.stage_id for stage in pipeline.stages])

    def test_global_video_renderer_remains_for_non_segmented_projects(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Project("Demo", Path(temp)).initialize()
            project.set_setting("pipeline_episode_segmentation_enabled", False)
            project.set_setting("pipeline_translation_enabled", True)
            project.set_setting("translation_target_language", "en")
            project.set_setting("pipeline_video_enabled", True)
            pipeline = build_project_pipeline(project, translator=FakeTranslator(), renderer=FakeRenderer(), ai_manager=FakeAIManager())
            self.assertEqual([stage.stage_id for stage in pipeline.stages], ["ocr", "translation", "ai_script", "narration", "video"])

    def test_all_stages_can_be_disabled(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Project("Demo", Path(temp)).initialize()
            project.set_setting("pipeline_ocr_enabled", False)
            project.set_setting("pipeline_ai_ocr_cleanup_enabled", False)
            project.set_setting("pipeline_hindi_spelling_correction_enabled", False)
            project.set_setting("pipeline_hindi_grammar_correction_enabled", False)
            project.set_setting("pipeline_ai_script_enabled", False)
            project.set_setting("pipeline_story_intelligence_enabled", False)
            project.set_setting("pipeline_scene_director_enabled", False)
            project.set_setting("pipeline_episode_segmentation_enabled", False)
            project.set_setting("pipeline_narration_enabled", False)
            with self.assertRaises(ValueError):
                build_project_pipeline(project, ai_manager=FakeAIManager())


if __name__ == "__main__":
    unittest.main()
