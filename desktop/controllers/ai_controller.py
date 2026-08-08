from __future__ import annotations

from threading import Event

from backend.ai import AIManager, AIRequest, AIStreamInterruptedError
from desktop.ai.configuration import AIProfile


class AIDesktopController:
    """UI-facing synchronous facade; Qt workers may call it off the UI thread."""

    def __init__(self, manager: AIManager | None = None):
        self.manager = manager or AIManager()
        self._cancelled = Event()

    def configure(self, profile: AIProfile) -> AIProfile:
        value = profile.normalized()
        self.manager.config = value.to_ai_config()
        return value

    def providers(self) -> list[str]:
        return self.manager.providers()

    def health_check(self, provider: str) -> tuple[bool, str]:
        return self.manager.health_check(provider)

    def discover_models(self, provider: str) -> list[str]:
        return self.manager.list_models(provider)

    def prompt_names(self) -> list[str]:
        return self.manager.list_prompts()

    @staticmethod
    def prompt_variables(template: str, text: str) -> dict:
        variables = {"text": text}
        defaults = {
            "translation": {"source_language": "auto", "target_language": "Hindi"},
            "chapter_summary": {"language": "Hindi", "audience": "general readers"},
            "script_generation": {"language": "Hindi", "tone": "natural narration"},
            "subtitle_generation": {"language": "Hindi"},
            "metadata_generation": {"language": "Hindi"},
            "content_rewrite": {"tone": "clear", "audience": "general readers"},
            "narration_assistant": {"language": "Hindi"},
            "ocr_cleanup": {"language": "original-language"},
        }
        variables.update(defaults.get(template, {}))
        return variables

    def generate(self, prompt: str, *, provider: str, model: str) -> str:
        value = str(prompt).strip()
        if not value:
            raise ValueError("Prompt is required.")
        self._cancelled.clear()
        response = self.manager.generate(
            AIRequest.from_prompt(value, model=str(model).strip()),
            provider_id=provider,
        )
        return response.text

    def stream(self, prompt: str, *, provider: str, model: str):
        value = str(prompt).strip()
        if not value:
            raise ValueError("Prompt is required.")
        self._cancelled.clear()
        try:
            for chunk in self.manager.stream(
                AIRequest.from_prompt(value, model=str(model).strip()),
                provider_id=provider,
            ):
                if self._cancelled.is_set():
                    return
                yield chunk
        except AIStreamInterruptedError:
            raise

    def stream_prompt(self, template: str, text: str, *, provider: str, model: str):
        value = str(text).strip()
        if not value:
            raise ValueError("Input text is required.")
        self._cancelled.clear()
        for chunk in self.manager.stream_prompt(
            template,
            self.prompt_variables(template, value),
            provider_id=provider,
            model=str(model).strip(),
        ):
            if self._cancelled.is_set():
                return
            yield chunk

    def cancel(self) -> None:
        self._cancelled.set()

    @property
    def cancelled(self) -> bool:
        return self._cancelled.is_set()
