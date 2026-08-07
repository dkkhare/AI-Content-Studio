from __future__ import annotations

from hashlib import sha1
from pathlib import Path
from typing import Any

from backend.images import VisualAssetReviewStore
from backend.knowledge import KnowledgeStore
from backend.scenes import SceneReviewStore

from .local_provider import VideoGenerationRequest


class SceneVideoService:
    """Generate one local video clip for every approved visual scene."""

    def __init__(self, project_root: str | Path, provider, *, fps: int = 24, width: int = 1920, height: int = 1080):
        self.root = Path(project_root).resolve()
        self.provider = provider
        self.fps = int(fps)
        self.width = int(width)
        self.height = int(height)
        self.knowledge = KnowledgeStore(self.root)
        self.knowledge.initialize()
        self.scene_review = SceneReviewStore(self.root)
        self.visual_review = VisualAssetReviewStore(self.root)

    @staticmethod
    def _asset_id(scene_id: str) -> str:
        digest = sha1(f"scene_video|{scene_id}".encode("utf-8")).hexdigest()[:12]
        return f"asset_{digest}"

    def _approved_scene_image(self, scene_id: str) -> dict[str, Any] | None:
        for item in self.visual_review.items():
            if (
                str(item.get("asset_type", "")) == "scene_image"
                and str(item.get("owner_id", "")) == scene_id
                and bool(item.get("approved", False))
            ):
                return item
        return None

    def _persist(self, item: dict[str, Any]) -> dict[str, Any]:
        existing = next(
            (row for row in self.knowledge.read("assets") if isinstance(row, dict) and row.get("id") == item.get("id")),
            {},
        )
        saved = dict(existing)
        saved.update(item)
        saved["approved"] = False
        saved["status"] = "pending_review"
        return self.knowledge.upsert("assets", saved)

    def generate_scene_clips(self, *, force: bool = False, progress=None) -> list[dict[str, Any]]:
        if not self.scene_review.review_complete():
            raise ValueError("Scene Review must be complete before local video generation.")
        if not self.visual_review.scene_review_complete():
            raise ValueError("Visual Review must be complete before local video generation.")

        scenes = self.scene_review.approved()
        results: list[dict[str, Any]] = []
        for index, scene in enumerate(scenes, start=1):
            scene_id = str(scene.get("id", ""))
            if not scene_id:
                continue
            image_asset = self._approved_scene_image(scene_id)
            if image_asset is None:
                raise ValueError(f"Approved scene has no approved image: {scene_id}")

            asset_id = self._asset_id(scene_id)
            existing = next(
                (row for row in self.knowledge.read("assets") if isinstance(row, dict) and row.get("id") == asset_id),
                None,
            )
            if existing and bool(existing.get("approved", False)) and not force:
                results.append(dict(existing))
                continue

            episode_id = str(scene.get("episode_id", "episode"))
            output = self.root / "segments" / episode_id / "video" / "clips" / f"{scene_id}.mp4"
            image = self.root / str(image_asset.get("path", ""))
            prompt = str(scene.get("video_prompt", scene.get("visual_description", scene.get("summary", "")))).strip()
            if not prompt:
                raise ValueError(f"Approved scene has no video prompt: {scene_id}")
            duration = float(scene.get("duration_seconds", 5.0) or 5.0)
            generated = self.provider.generate(
                VideoGenerationRequest(
                    prompt=prompt,
                    output=output,
                    image=image,
                    duration_seconds=max(1.0, duration),
                    fps=self.fps,
                    width=self.width,
                    height=self.height,
                )
            )
            record = self._persist(
                {
                    "id": asset_id,
                    "asset_type": "scene_video",
                    "owner_id": scene_id,
                    "episode_id": episode_id,
                    "prompt": prompt,
                    "source_image_path": str(image.relative_to(self.root)),
                    "duration_seconds": max(1.0, duration),
                    "path": str(Path(generated).relative_to(self.root)),
                    "provider": str(getattr(self.provider, "provider_id", "local-command")),
                }
            )
            results.append(record)
            if progress:
                progress(round(index / max(1, len(scenes)) * 100), f"Generated scene clip {index} of {len(scenes)}")
        return results
