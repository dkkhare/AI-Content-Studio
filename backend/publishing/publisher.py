from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .providers import ManualPublishingProvider, PublishingProvider, YouTubePublishingProvider
from .release import ReleaseManager


class PublishingService:
    """Publish Ready episodes through a configured provider and persist release outcomes."""

    def __init__(self, project, providers: dict[str, PublishingProvider] | None = None):
        self.project = project
        self.root = Path(project.root).resolve()
        self.releases = ReleaseManager(self.root)
        self.providers = providers or self._default_providers()

    def _default_providers(self) -> dict[str, PublishingProvider]:
        return {
            "manual": ManualPublishingProvider(),
            "youtube": YouTubePublishingProvider(
                client_secrets_path=str(self.project.get_setting("youtube_client_secrets_path", "") or ""),
                token_path=str(self.project.get_setting("youtube_token_path", "") or ""),
            ),
        }

    def provider(self, provider_id: str) -> PublishingProvider:
        key = str(provider_id or "").strip().lower()
        if key not in self.providers:
            raise ValueError(f"Unknown publishing provider: {provider_id}")
        return self.providers[key]

    def provider_status(self) -> list[dict[str, Any]]:
        return [
            {"id": provider_id, "name": provider.display_name, "configured": bool(provider.configured()), "error": provider.configuration_error()}
            for provider_id, provider in self.providers.items()
        ]

    def _manifest_for_release(self, episode_id: str) -> dict[str, Any]:
        manifest = copy.deepcopy(self.releases.manifest(episode_id))
        release = self.releases.get(episode_id)
        youtube = manifest.setdefault("youtube", {})
        if isinstance(youtube, dict):
            youtube["publish_at"] = str(release.get("scheduled_publish_at", "") or "")
            youtube["playlist_id"] = str(release.get("playlist_id", "") or "")
        return manifest

    def publish_episode(self, episode_id: str, provider_id: str) -> dict[str, Any]:
        release = self.releases.get(episode_id)
        if str(release.get("state", "draft")) != "ready":
            raise ValueError("Episode must be Ready before provider publishing can start.")
        provider = self.provider(provider_id)
        if not provider.configured():
            raise ValueError(provider.configuration_error() or f"Provider is not configured: {provider_id}")
        manifest = self._manifest_for_release(episode_id)
        try:
            result = provider.publish(manifest, root=self.root)
        except Exception as exc:
            self.releases.mark_failed(episode_id, str(exc), note=f"Publishing provider failed: {provider_id}")
            raise
        return self.releases.mark_published(
            episode_id,
            destination=result.destination or provider_id,
            external_id=result.external_id,
            external_url=result.external_url,
            note=f"Published through provider: {provider_id}",
        )

    def publish_ready(self, provider_id: str, *, stop_on_error: bool = False) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for item in self.releases.items():
            if str(item.get("state", "draft")) != "ready":
                continue
            episode_id = str(item.get("episode_id", ""))
            try:
                release = self.publish_episode(episode_id, provider_id)
                results.append({"episode_id": episode_id, "ok": True, "release": release})
            except Exception as exc:
                results.append({"episode_id": episode_id, "ok": False, "error": str(exc)})
                if stop_on_error:
                    break
        return results
