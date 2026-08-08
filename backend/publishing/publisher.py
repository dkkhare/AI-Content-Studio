from __future__ import annotations

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
        rows = []
        for provider_id, provider in self.providers.items():
            rows.append({
                "id": provider_id,
                "name": provider.display_name,
                "configured": bool(provider.configured()),
                "error": provider.configuration_error(),
            })
        return rows

    def publish_episode(self, episode_id: str, provider_id: str) -> dict[str, Any]:
        release = self.releases.get(episode_id)
        if str(release.get("state", "draft")) != "ready":
            raise ValueError("Episode must be Ready before provider publishing can start.")
        provider = self.provider(provider_id)
        if not provider.configured():
            raise ValueError(provider.configuration_error() or f"Provider is not configured: {provider_id}")
        manifest = self.releases.manifest(episode_id)
        try:
            result = provider.publish(manifest, root=self.root)
        except Exception as exc:
            self.releases.mark_failed(
                episode_id,
                str(exc),
                note=f"Publishing provider failed: {provider_id}",
            )
            raise
        return self.releases.mark_published(
            episode_id,
            destination=result.destination or provider_id,
            external_id=result.external_id,
            external_url=result.external_url,
            note=f"Published through provider: {provider_id}",
        )
