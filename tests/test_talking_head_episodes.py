from __future__ import annotations

import unittest

from backend.talking_head import SourceBlock, plan_episodes


def words(count, final="."):
    return " ".join(f"word{i}" for i in range(count)) + final


class EpisodePlannerTests(unittest.TestCase):
    def test_preserves_every_source_block_once_and_in_order(self):
        blocks = [
            SourceBlock("chapter-1", "Chapter One", words(900)),
            SourceBlock("chapter-2", "Chapter Two", words(900)),
            SourceBlock("chapter-3", "Chapter Three", words(500)),
        ]
        plan = plan_episodes(blocks, target_minutes=10, words_per_minute=120)
        plan.validate_coverage()
        encountered = []
        for episode in plan.episodes:
            for fragment in episode.fragments:
                if fragment.source_id not in encountered:
                    encountered.append(fragment.source_id)
        self.assertEqual(encountered, [item.block_id for item in blocks])
        self.assertGreaterEqual(len(plan.episodes), 2)

    def test_prefers_chapter_boundary_near_target(self):
        blocks = [
            SourceBlock("one", "Chapter One", words(1000)),
            SourceBlock("two", "Chapter Two", words(1000)),
        ]
        plan = plan_episodes(blocks, target_minutes=10, words_per_minute=120)
        self.assertEqual(len(plan.episodes), 2)
        self.assertEqual(plan.episodes[0].title, "Chapter One")
        self.assertEqual(plan.episodes[1].title, "Chapter Two")

    def test_long_chapter_is_split_and_continuation_is_titled(self):
        sentences = " ".join(words(240) for _ in range(10))
        plan = plan_episodes(
            [SourceBlock("long", "A Long Chapter", sentences)],
            target_minutes=5,
            words_per_minute=120,
        )
        self.assertGreater(len(plan.episodes), 1)
        self.assertIn("Part 2", plan.episodes[1].title)
        plan.validate_coverage()

    def test_rejects_duplicate_ids_and_unsafe_duration(self):
        with self.assertRaisesRegex(ValueError, "unique"):
            plan_episodes(
                [SourceBlock("x", "One", "text."), SourceBlock("x", "Two", "text.")]
            )
        with self.assertRaisesRegex(ValueError, "between 5 and 60"):
            plan_episodes([SourceBlock("x", "One", "text.")], target_minutes=2)


if __name__ == "__main__":
    unittest.main()
