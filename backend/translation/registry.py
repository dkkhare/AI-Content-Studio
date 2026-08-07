from __future__ import annotations

from .google_provider import GoogleTranslationProvider


def create_translation_provider(project):
    """Create the configured translation provider for a project."""

    provider = str(project.get_setting("translation_provider", "google")).strip().lower()
    api_key_env = str(
        project.get_setting("translation_api_key_env", "GOOGLE_TRANSLATE_API_KEY")
    ).strip() or "GOOGLE_TRANSLATE_API_KEY"

    if provider == "google":
        return GoogleTranslationProvider(api_key_env=api_key_env)

    raise ValueError(f"Unsupported translation provider: {provider}")
