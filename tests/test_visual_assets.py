from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.images import VisualAssetReviewStore, VisualAssetService
from backend.knowledge import KnowledgeStore


class FakeImageProvider:
    def __init__(self):
        self.calls = []

    def generate(self, **kwargs):
        self.calls.append(dict(kwargs))
        output = Path(kwargs["output"])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"png")
        return output


class VisualAssetTests(unittest.TestCase):
    def test_reference_images_are_generated_for_approved_entities_only(self):
        with tempfile.TemporaryDirectory() as temp:
            store = KnowledgeStore(temp)
            store.initialize()
            store.write("characters", [
                {"id": "char_1", "name": "मोहन", "appearance": "नीला कुर्ता", "approved": True},
                {"id": "char_2", "name": "सोहन", "approved": False},
            ])
            store.write("locations", [{"id": "loc_1", "name": "गाँव", "description": "भारतीय गाँव", "approved": True}])
            provider = FakeImageProvider()
            assets = VisualAssetService(temp, provider).generate_references()
            self.assertEqual(len(assets), 2)
            self.assertEqual(len(provider.calls), 2)
            self.assertTrue(all(item["status"] == "pending_review" for item in assets))

    def test_scene_generation_reuses_only_approved_reference_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = KnowledgeStore(root)
            store.initialize()
            store.write("characters", [{"id": "char_1", "name": "मोहन", "approved": True}])
            store.write("locations", [{"id": "loc_1", "name": "गाँव", "approved": True}])
            provider = FakeImageProvider()
            service = VisualAssetService(root, provider)
            references = service.generate_references()
            review = VisualAssetReviewStore(root)
            for asset in references:
                review.approve(asset["id"])

            store.write("scenes", [{
                "id": "scene_1",
                "episode_id": "episode_001",
                "approved": True,
                "image_prompt": "मोहन गाँव में चलता है",
                "character_ids": ["char_1"],
                "location_id": "loc_1",
            }])
            assets = service.generate_scene_images()
            self.assertEqual(len(assets), 1)
            self.assertEqual(len(provider.calls[-1]["references"]), 2)
            self.assertTrue((root / assets[0]["path"]).exists())
            self.assertFalse(assets[0]["approved"])

    def test_visual_review_requires_explicit_approval_or_skip(self):
        with tempfile.TemporaryDirectory() as temp:
            store = KnowledgeStore(temp)
            store.initialize()
            store.write("assets", [
                {"id": "a1", "asset_type": "character_reference", "approved": False, "status": "pending_review"},
                {"id": "a2", "asset_type": "location_reference", "approved": False, "status": "pending_review"},
            ])
            review = VisualAssetReviewStore(temp)
            self.assertFalse(review.reference_review_complete())
            review.approve("a1")
            review.skip("a2")
            self.assertTrue(review.reference_review_complete())


if __name__ == "__main__":
    unittest.main()
