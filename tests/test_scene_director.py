from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from backend.ai import AIResponse
from backend.episodes import EpisodeReviewStore, SegmentPlanner
from backend.knowledge import KnowledgeReviewStore, KnowledgeStore
from backend.scenes import SceneDirectorService, SceneReviewStore


class FakeAIManager:
    def __init__(self):
        self.calls = []

    def execute_prompt(self, name, variables=None, **kwargs):
        self.calls.append((name, variables or {}, kwargs))
        payload = {
            "scenes": [
                {
                    "narration": "मोहन गाँव की ओर चला।",
                    "estimated_seconds": 35,
                    "summary": "मोहन गाँव की ओर चलता है",
                    "characters": ["मोहन"],
                    "location": "गाँव",
                    "objects": [],
                    "mood": "शांत",
                    "time_of_day": "सुबह",
                    "camera": "wide tracking shot",
                    "visual_description": "सुबह के गाँव में मोहन चलता हुआ",
                    "image_prompt": "cinematic Indian village morning, Mohan walking",
                    "video_prompt": "slow tracking shot of Mohan walking through village",
                    "transition": "fade",
                },
                {
                    "narration": "वह मंदिर के सामने रुका।",
                    "estimated_seconds": 25,
                    "summary": "मोहन मंदिर के सामने रुकता है",
                    "characters": ["मोहन"],
                    "location": "मंदिर",
                    "objects": [],
                    "mood": "विचारशील",
                    "camera": "medium shot",
                    "visual_description": "मंदिर के सामने खड़ा मोहन",
                    "image_prompt": "Mohan standing before Indian temple",
                    "video_prompt": "gentle push-in toward Mohan at temple",
                    "transition": "cut",
                },
            ]
        }
        return AIResponse(text=json.dumps(payload, ensure_ascii=False), provider="fake", model="fake-model")


class SceneDirectorTests(unittest.TestCase):
    def _project(self, root: Path):
        planner = SegmentPlanner(target_minutes=1, min_minutes=1, max_minutes=2, words_per_minute=20)
        episodes = planner.plan("अध्याय 1\n\nमोहन गाँव की ओर चला। वह मंदिर के सामने रुका। " * 6)
        planner.persist(root, episodes)
        episode_store = EpisodeReviewStore(root)
        episode_id = str(episode_store.episodes()[0]["episode_id"])
        episode_store.approve(episode_id)
        knowledge = KnowledgeStore(root)
        knowledge.initialize()
        knowledge.write("characters", [{"id": "char_1", "name": "मोहन", "approved": True, "status": "approved"}])
        knowledge.write("locations", [
            {"id": "loc_1", "name": "गाँव", "approved": True, "status": "approved"},
            {"id": "loc_2", "name": "मंदिर", "approved": True, "status": "approved"},
        ])
        return episode_id, knowledge

    def test_scene_director_persists_reviewable_scenes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            episode_id, knowledge = self._project(root)
            ai = FakeAIManager()
            service = SceneDirectorService(root, ai)
            plan = service.plan_episode(episode_id)
            self.assertEqual(plan["scene_count"], 2)
            self.assertEqual(plan["status"], "review_required")
            scenes = SceneReviewStore(root).scenes(episode_id)
            self.assertEqual(len(scenes), 2)
            self.assertTrue(all(not item["approved"] for item in scenes))
            self.assertEqual(ai.calls[0][0], "scene_director")
            knowledge_payload = json.loads(ai.calls[0][1]["knowledge_json"])
            self.assertEqual(knowledge_payload["characters"][0]["name"], "मोहन")

    def test_scene_review_approve_edit_skip_and_plan_sync(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            episode_id, _ = self._project(root)
            SceneDirectorService(root, FakeAIManager()).plan_episode(episode_id)
            review = SceneReviewStore(root)
            scenes = review.scenes(episode_id)
            review.approve(scenes[0]["id"])
            edited = review.edit(scenes[1]["id"], {"camera": "close-up"})
            self.assertEqual(edited["camera"], "close-up")
            self.assertEqual(edited["status"], "edited")
            self.assertFalse(review.review_complete(episode_id))
            review.skip(scenes[1]["id"])
            self.assertTrue(review.review_complete(episode_id))
            plan = KnowledgeStore(root).read("scene_plans")[0]
            self.assertTrue(plan["approved"])
            self.assertEqual(plan["status"], "approved")

    def test_pending_story_review_blocks_scene_planning(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            episode_id, knowledge = self._project(root)
            knowledge.write("objects", [{"id": "obj_1", "name": "घंटी", "approved": False, "status": "pending_review"}])
            self.assertFalse(KnowledgeReviewStore(root).review_complete())
            with self.assertRaises(ValueError):
                SceneDirectorService(root, FakeAIManager()).plan_episode(episode_id)


if __name__ == "__main__":
    unittest.main()
