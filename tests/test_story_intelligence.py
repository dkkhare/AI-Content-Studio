from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from backend.ai import AIResponse
from backend.episodes import EpisodeReviewStore, SegmentPlanner
from backend.knowledge import KnowledgeStore
from backend.story import StoryIntelligenceService


class FakeAIManager:
    def __init__(self, payload):
        self.payload = payload
        self.calls = 0

    def execute_prompt(self, name, variables=None, **kwargs):
        self.calls += 1
        self.last_name = name
        self.last_variables = dict(variables or {})
        return AIResponse(
            text=json.dumps(self.payload, ensure_ascii=False),
            provider="ollama",
            model="test-model",
        )


class StoryIntelligenceTests(unittest.TestCase):
    def _approved_episode(self, root: Path, text: str = "अध्याय 1\n\nराम वन में गए।") -> str:
        planner = SegmentPlanner(target_minutes=5, min_minutes=1, max_minutes=10, words_per_minute=130)
        episodes = planner.plan(text)
        planner.persist(root, episodes)
        store = EpisodeReviewStore(root)
        episode_id = str(store.episodes()[0]["episode_id"])
        store.approve(episode_id)
        return episode_id

    def _payload(self):
        return {
            "genre": "कथा",
            "time_period": "",
            "mood": "शांत",
            "characters": [
                {
                    "name": "राम",
                    "aliases": ["श्रीराम"],
                    "role": "मुख्य पात्र",
                    "importance": "main",
                    "appearance": "",
                    "personality": "धैर्यवान",
                }
            ],
            "locations": [
                {
                    "name": "वन",
                    "aliases": [],
                    "type": "प्राकृतिक स्थान",
                    "description": "जंगल",
                }
            ],
            "objects": [{"name": "धनुष", "aliases": [], "description": "", "importance": ""}],
            "relationships": [],
            "events": [{"summary": "राम वन में गए", "characters": ["राम"], "location": "वन", "time": ""}],
            "scene_candidates": [{"summary": "राम का वन में प्रवेश", "characters": ["राम"], "location": "वन", "mood": "शांत", "visual_notes": ""}],
        }

    def test_analyzes_only_approved_episode_and_persists_knowledge(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            episode_id = self._approved_episode(root)
            manager = FakeAIManager(self._payload())
            service = StoryIntelligenceService(root, manager)

            result = service.analyze_episode(episode_id)
            store = KnowledgeStore(root)

            self.assertEqual(manager.calls, 1)
            self.assertEqual(manager.last_name, "story_intelligence")
            self.assertEqual(result["episode_id"], episode_id)
            self.assertEqual(len(store.read("characters")), 1)
            self.assertEqual(store.read("characters")[0]["status"], "pending_review")
            self.assertFalse(store.read("characters")[0]["approved"])
            self.assertEqual(len(store.read("locations")), 1)
            self.assertEqual(len(store.read("objects")), 1)
            self.assertEqual(len(store.read("events")), 1)
            self.assertEqual(len(store.read("timeline")), 1)
            self.assertEqual(len(store.read("scenes")), 1)
            self.assertEqual(store.read("scenes")[0]["status"], "candidate")
            self.assertEqual(len(store.read("analyses")), 1)

    def test_unchanged_episode_is_not_reanalyzed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            episode_id = self._approved_episode(root)
            manager = FakeAIManager(self._payload())
            service = StoryIntelligenceService(root, manager)

            first = service.analyze_episode(episode_id)
            second = service.analyze_episode(episode_id)

            self.assertEqual(manager.calls, 1)
            self.assertEqual(first["script_sha256"], second["script_sha256"])

    def test_unapproved_episode_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            planner = SegmentPlanner(target_minutes=5, min_minutes=1, max_minutes=10, words_per_minute=130)
            episodes = planner.plan("अध्याय 1\n\nराम वन में गए।")
            planner.persist(root, episodes)
            episode_id = str(EpisodeReviewStore(root).episodes()[0]["episode_id"])
            service = StoryIntelligenceService(root, FakeAIManager(self._payload()))

            with self.assertRaises(ValueError):
                service.analyze_episode(episode_id)

    def test_similar_honorific_name_creates_merge_suggestion_not_auto_merge(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            episode_id = self._approved_episode(root)
            store = KnowledgeStore(root)
            store.initialize()
            store.upsert(
                "characters",
                {
                    "id": "character_existing",
                    "name": "श्रीराम",
                    "aliases": [],
                    "approved": True,
                    "status": "approved",
                },
            )
            manager = FakeAIManager(self._payload())
            StoryIntelligenceService(root, manager).analyze_episode(episode_id)

            characters = store.read("characters")
            suggestions = store.read("merge_suggestions")
            self.assertEqual(len(characters), 2)
            self.assertEqual(len(suggestions), 1)
            self.assertEqual(suggestions[0]["status"], "pending")
            self.assertEqual(suggestions[0]["entity_type"], "character")


if __name__ == "__main__":
    unittest.main()
