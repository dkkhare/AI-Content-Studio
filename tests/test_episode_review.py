from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.episodes import EpisodeReviewStore, SegmentPlanner


class EpisodeReviewStoreTests(unittest.TestCase):
    def _store(self, root: Path) -> EpisodeReviewStore:
        planner = SegmentPlanner(
            target_minutes=1,
            min_minutes=1,
            max_minutes=2,
            words_per_minute=20,
        )
        text = (
            "अध्याय 1\n\n"
            + "पहला " * 25
            + "।\n\nअध्याय 2\n\n"
            + "दूसरा " * 25
            + "।"
        )
        planner.persist(root, planner.plan(text))
        return EpisodeReviewStore(root)

    def test_edit_recalculates_duration_and_requires_reapproval(self):
        with tempfile.TemporaryDirectory() as temp:
            store = self._store(Path(temp))
            episode_id = str(store.episodes()[0]["episode_id"])
            store.approve(episode_id)
            edited = store.edit(
                episode_id,
                title="नया शीर्षक",
                text="शब्द " * 40,
            )
            self.assertEqual(edited["title"], "नया शीर्षक")
            self.assertEqual(edited["word_count"], 40)
            self.assertAlmostEqual(edited["estimated_minutes"], 2.0)
            self.assertFalse(edited["approved"])
            self.assertEqual(edited["status"], "edited")
            self.assertIn("शब्द", store.script(episode_id))

    def test_review_complete_accepts_approved_or_skipped(self):
        with tempfile.TemporaryDirectory() as temp:
            store = self._store(Path(temp))
            episodes = store.episodes()
            self.assertFalse(store.review_complete())
            for index, episode in enumerate(episodes):
                episode_id = str(episode["episode_id"])
                if index == len(episodes) - 1:
                    store.skip(episode_id)
                else:
                    store.approve(episode_id)
            self.assertTrue(store.review_complete())
            self.assertEqual(len(store.pending()), 0)
            self.assertEqual(
                len(store.approved()),
                max(0, len(episodes) - 1),
            )

    def test_regeneration_request_is_not_approved(self):
        with tempfile.TemporaryDirectory() as temp:
            store = self._store(Path(temp))
            episode_id = str(store.episodes()[0]["episode_id"])
            updated = store.request_regeneration(episode_id)
            self.assertEqual(updated["status"], "regenerate_requested")
            self.assertFalse(updated["approved"])
            self.assertFalse(store.review_complete())


if __name__ == "__main__":
    unittest.main()
