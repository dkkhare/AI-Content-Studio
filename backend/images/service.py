from __future__ import annotations

from hashlib import sha1
from pathlib import Path
from typing import Any

from backend.knowledge import KnowledgeStore


class VisualAssetService:
    """Generate reusable references first, then approved scene images."""

    def __init__(self, project_root: str | Path, provider):
        self.root = Path(project_root).resolve()
        self.provider = provider
        self.knowledge = KnowledgeStore(self.root)
        self.knowledge.initialize()

    @staticmethod
    def _asset_id(asset_type: str, owner_id: str) -> str:
        digest = sha1(f"{asset_type}|{owner_id}".encode("utf-8")).hexdigest()[:12]
        return f"asset_{digest}"

    def _approved(self, collection: str) -> list[dict[str, Any]]:
        return [
            item for item in self.knowledge.read(collection)
            if isinstance(item, dict) and bool(item.get("approved", False))
        ]

    def _style_suffix(self) -> str:
        style = self.knowledge.read("style")
        if not isinstance(style, dict):
            return ""
        text = str(style.get("visual_style", style.get("description", ""))).strip()
        return f", consistent visual style: {text}" if text else ""

    def _persist_asset(self, item: dict[str, Any]) -> dict[str, Any]:
        existing = next(
            (row for row in self.knowledge.read("assets") if isinstance(row, dict) and row.get("id") == item.get("id")),
            {},
        )
        saved = dict(existing)
        saved.update(item)
        if not existing:
            saved.setdefault("approved", False)
            saved.setdefault("status", "pending_review")
        else:
            saved["approved"] = False
            saved["status"] = "pending_review"
        return self.knowledge.upsert("assets", saved)

    def generate_references(self, *, force: bool = False, progress=None) -> list[dict[str, Any]]:
        entities = [
            ("characters", "character_reference", self._approved("characters")),
            ("locations", "location_reference", self._approved("locations")),
        ]
        work = [(collection, asset_type, item) for collection, asset_type, values in entities for item in values]
        results = []
        for index, (collection, asset_type, item) in enumerate(work, start=1):
            owner_id = str(item.get("id", ""))
            if not owner_id:
                continue
            asset_id = self._asset_id(asset_type, owner_id)
            existing = next(
                (row for row in self.knowledge.read("assets") if isinstance(row, dict) and row.get("id") == asset_id),
                None,
            )
            if existing and bool(existing.get("approved", False)) and not force:
                results.append(dict(existing))
                continue
            folder = "characters" if collection == "characters" else "locations"
            output = self.root / "visuals" / "references" / folder / owner_id / "reference.png"
            description = str(item.get("appearance", item.get("description", ""))).strip()
            prompt = f"Reference image for {item.get('name', owner_id)}. {description}{self._style_suffix()}".strip()
            generated = self.provider.generate(prompt=prompt, output=output, width=1024, height=1024)
            record = self._persist_asset(
                {
                    "id": asset_id,
                    "asset_type": asset_type,
                    "owner_id": owner_id,
                    "owner_collection": collection,
                    "prompt": prompt,
                    "path": str(Path(generated).relative_to(self.root)),
                }
            )
            results.append(record)
            if progress:
                progress(round(index / max(1, len(work)) * 100), f"Generated reference {index} of {len(work)}")
        return results

    def _approved_reference_paths(self, owner_ids: list[str]) -> list[str]:
        paths = []
        for item in self.knowledge.read("assets"):
            if not isinstance(item, dict) or not bool(item.get("approved", False)):
                continue
            if str(item.get("asset_type", "")) not in {"character_reference", "location_reference"}:
                continue
            if str(item.get("owner_id", "")) not in owner_ids:
                continue
            raw = str(item.get("path", ""))
            if raw:
                paths.append(str((self.root / raw).resolve()))
        return paths

    def generate_scene_images(self, *, force: bool = False, progress=None) -> list[dict[str, Any]]:
        scenes = [
            item for item in self.knowledge.read("scenes")
            if isinstance(item, dict) and bool(item.get("approved", False))
        ]
        results = []
        for index, scene in enumerate(scenes, start=1):
            scene_id = str(scene.get("id", ""))
            if not scene_id:
                continue
            asset_id = self._asset_id("scene_image", scene_id)
            existing = next(
                (row for row in self.knowledge.read("assets") if isinstance(row, dict) and row.get("id") == asset_id),
                None,
            )
            if existing and bool(existing.get("approved", False)) and not force:
                results.append(dict(existing))
                continue
            episode_id = str(scene.get("episode_id", "episode"))
            output = self.root / "segments" / episode_id / "images" / f"{scene_id}.png"
            character_ids = [str(v) for v in scene.get("character_ids", []) if str(v)]
            location_id = str(scene.get("location_id", ""))
            owners = character_ids + ([location_id] if location_id else [])
            references = self._approved_reference_paths(owners)
            prompt = str(scene.get("image_prompt", scene.get("visual_description", scene.get("summary", "")))).strip()
            if not prompt:
                raise ValueError(f"Approved scene has no image prompt: {scene_id}")
            generated = self.provider.generate(
                prompt=prompt + self._style_suffix(),
                output=output,
                references=references,
                width=1920,
                height=1080,
            )
            record = self._persist_asset(
                {
                    "id": asset_id,
                    "asset_type": "scene_image",
                    "owner_id": scene_id,
                    "episode_id": episode_id,
                    "prompt": prompt,
                    "reference_paths": references,
                    "path": str(Path(generated).relative_to(self.root)),
                }
            )
            results.append(record)
            if progress:
                progress(round(index / max(1, len(scenes)) * 100), f"Generated scene image {index} of {len(scenes)}")
        return results
