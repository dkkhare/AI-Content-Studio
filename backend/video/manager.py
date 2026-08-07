from __future__ import annotations

from pathlib import Path

from .local_provider import LocalCommandVideoProvider, VideoGenerationRequest


class VideoGenerationManager:
    """Small local-first video generation facade used by pipeline stages."""

    def __init__(self, provider: LocalCommandVideoProvider):
        self.provider = provider

    @classmethod
    def from_project(cls, project) -> "VideoGenerationManager":
        provider_name = str(project.get_setting("video_generator_provider", "local-command") or "local-command")
        if provider_name != "local-command":
            raise ValueError(
                f"Unsupported local video generator provider: {provider_name}. "
                "Use local-command for a locally installed open-source generator."
            )

        command = str(project.get_setting("video_generator_command", "") or "")
        args_template = str(project.get_setting("video_generator_args", "") or "")
        return cls(LocalCommandVideoProvider(command, args_template))

    def generate(
        self,
        prompt: str,
        output: str | Path,
        image: str | Path | None = None,
    ) -> Path:
        request = VideoGenerationRequest(
            prompt=str(prompt),
            output=Path(output),
            image=Path(image) if image else None,
        )
        return self.provider.generate(request)
