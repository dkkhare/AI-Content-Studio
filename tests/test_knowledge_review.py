from __future__ import annotations

import tempfile
import unittest

from backend.knowledge import KnowledgeReviewStore, KnowledgeStore


class KnowledgeReviewTests(unittest.TestCase):
    def test_approve_edit_and_skip_are_independent(self):
        with tempfile.TemporaryDirectory() as temp:
            store = KnowledgeStore(temp)
            store.initialize()
            store.write("characters", [
                {"id": "char_1", "name": "मोहन", "approved": False, "status": "pending_review"},
                {"id": "char_2", "name": "सीता", "approved": False, "status": "pending_review"},
            ])
            review = KnowledgeReviewStore(temp)
            review.approve("characters", "char_1")
            review.edit("characters", "char_1", {"description": "मुख्य पात्र"})
            edited = review.get("characters", "char_1")
            self.assertFalse(edited["approved"])
            self.assertEqual(edited["status"], "edited")
            self.assertEqual(edited["description"], "मुख्य पात्र")
            review.skip("characters", "char_2")
            self.assertEqual(review.get("characters", "char_2")["status"], "skipped")
            self.assertEqual(len(review.pending("characters")), 1)

    def test_merge_preserves_aliases_and_appearances_and_resolves_suggestion(self):
        with tempfile.TemporaryDirectory() as temp:
            store = KnowledgeStore(temp)
            store.initialize()
            store.write("characters", [
                {"id": "char_a", "name": "राम", "aliases": ["रघुनंदन"], "episode_ids": ["episode_001"], "approved": True, "status": "approved"},
                {"id": "char_b", "name": "श्रीराम", "aliases": [], "episode_ids": ["episode_002"], "approved": False, "status": "pending_review"},
            ])
            store.write("merge_suggestions", [
                {"id": "merge_1", "entity_type": "character", "left_id": "char_a", "right_id": "char_b", "status": "pending"}
            ])
            review = KnowledgeReviewStore(temp)
            target = review.merge("characters", "char_b", "char_a")
            self.assertTrue(target["approved"])
            self.assertIn("श्रीराम", target["aliases"])
            self.assertEqual(set(target["episode_ids"]), {"episode_001", "episode_002"})
            source = review.get("characters", "char_b")
            self.assertEqual(source["status"], "merged")
            self.assertEqual(source["merged_into"], "char_a")
            suggestion = store.read("merge_suggestions")[0]
            self.assertEqual(suggestion["status"], "resolved")
            self.assertEqual(suggestion["merged_into"], "char_a")

    def test_review_complete_ignores_skipped_and_merged(self):
        with tempfile.TemporaryDirectory() as temp:
            store = KnowledgeStore(temp)
            store.initialize()
            store.write("characters", [{"id": "c1", "name": "अ", "approved": True, "status": "approved"}])
            store.write("locations", [{"id": "l1", "name": "गाँव", "approved": False, "status": "skipped"}])
            store.write("objects", [{"id": "o1", "name": "पुस्तक", "approved": False, "status": "merged"}])
            store.write("relationships", [{"id": "r1", "source": "अ", "target": "ब", "relationship": "मित्र", "approved": True, "status": "approved"}])
            review = KnowledgeReviewStore(temp)
            self.assertTrue(review.review_complete())


if __name__ == "__main__":
    unittest.main()
