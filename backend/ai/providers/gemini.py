from __future__ import annotations

import json
import os
from collections.abc import Iterable
from urllib import error, parse, request

from ..exceptions import AIConfigurationError, AIProviderError
from ..models import AIRequest, AIResponse, AIStreamChunk, AIUsage
from ..provider import AIProvider


class GeminiProvider(AIProvider):
    """Google Gemini REST adapter using generateContent endpoints."""

    provider_id = "gemini"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        api_key_env: str = "GEMINI_API_KEY",
        base_url: str | None = None,
        default_model: str | None = None,
        timeout: float = 60.0,
        opener=None,
    ):
        self.api_key_env = api_key_env
        self.api_key = api_key or os.getenv(api_key_env, "") or os.getenv("GOOGLE_API_KEY", "")
        self.base_url = (base_url or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
        self.default_model = default_model or os.getenv("GEMINI_MODEL", "")
        self.timeout = max(1.0, float(timeout))
        self._open = opener or request.urlopen

    def configured(self) -> bool:
        return bool(self.api_key)

    def capabilities(self) -> set[str]:
        return {"text", "streaming", "models"}

    def _model(self, value: AIRequest) -> str:
        model = value.model or self.default_model
        if not model:
            raise AIConfigurationError("Gemini request requires a model. Set GEMINI_MODEL or request.model.")
        return model.removeprefix("models/")

    def _key_query(self) -> str:
        if not self.configured():
            raise AIConfigurationError(
                f"Gemini API key is missing. Set environment variable {self.api_key_env}."
            )
        return parse.urlencode({"key": self.api_key})

    def _payload(self, value: AIRequest) -> dict:
        contents = []
        system_parts: list[dict[str, str]] = []
        for message in value.messages:
            if message.role == "system":
                system_parts.append({"text": message.content})
                continue
            role = "model" if message.role == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": message.content}]})

        payload: dict = {"contents": contents}
        if system_parts:
            payload["systemInstruction"] = {"parts": system_parts}

        generation: dict = {}
        if value.temperature is not None:
            generation["temperature"] = float(value.temperature)
        if value.max_output_tokens is not None:
            generation["maxOutputTokens"] = int(value.max_output_tokens)
        if generation:
            payload["generationConfig"] = generation
        return payload

    @staticmethod
    def _usage(data: dict | None) -> AIUsage:
        raw = (data or {}).get("usageMetadata") or {}
        return AIUsage(
            input_tokens=int(raw.get("promptTokenCount") or 0),
            output_tokens=int(raw.get("candidatesTokenCount") or 0),
            total_tokens=int(raw.get("totalTokenCount") or 0),
        )

    @staticmethod
    def _text(data: dict) -> str:
        parts: list[str] = []
        for candidate in data.get("candidates") or []:
            content = candidate.get("content") or {}
            for part in content.get("parts") or []:
                if isinstance(part, dict) and part.get("text") is not None:
                    parts.append(str(part.get("text") or ""))
        return "".join(parts)

    @staticmethod
    def _error_message(exc: error.HTTPError) -> str:
        try:
            data = json.loads(exc.read().decode("utf-8"))
            detail = str((data.get("error") or {}).get("message") or "").strip()
        except Exception:
            detail = ""
        return f"Gemini HTTP {exc.code}" + (f": {detail}" if detail else "")

    def generate(self, value: AIRequest) -> AIResponse:
        model = self._model(value)
        url = f"{self.base_url}/models/{model}:generateContent?{self._key_query()}"
        req = request.Request(
            url,
            data=json.dumps(self._payload(value)).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self._open(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            raise AIProviderError(self._error_message(exc)) from exc
        except (error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise AIProviderError(f"Gemini request failed: {exc}") from exc

        return AIResponse(
            text=self._text(data),
            provider=self.provider_id,
            model=model,
            usage=self._usage(data),
            raw=data,
        )

    def stream(self, value: AIRequest) -> Iterable[AIStreamChunk]:
        model = self._model(value)
        url = (
            f"{self.base_url}/models/{model}:streamGenerateContent?"
            f"alt=sse&{self._key_query()}"
        )
        req = request.Request(
            url,
            data=json.dumps(self._payload(value)).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
            method="POST",
        )
        last_usage: AIUsage | None = None
        try:
            with self._open(req, timeout=self.timeout) as response:
                for raw_line in response:
                    line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else str(raw_line)
                    line = line.strip()
                    if not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if not payload:
                        continue
                    try:
                        data = json.loads(payload)
                    except json.JSONDecodeError:
                        continue
                    text = self._text(data)
                    usage = self._usage(data)
                    if usage.total_tokens:
                        last_usage = usage
                    if text:
                        yield AIStreamChunk(
                            text=text,
                            provider=self.provider_id,
                            model=model,
                            raw=data,
                        )
            yield AIStreamChunk(
                provider=self.provider_id,
                model=model,
                done=True,
                usage=last_usage or AIUsage(),
            )
        except error.HTTPError as exc:
            raise AIProviderError(self._error_message(exc)) from exc
        except (error.URLError, TimeoutError, OSError) as exc:
            raise AIProviderError(f"Gemini streaming request failed: {exc}") from exc

    def list_models(self) -> list[str]:
        url = f"{self.base_url}/models?{self._key_query()}"
        req = request.Request(url, method="GET")
        try:
            with self._open(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            raise AIProviderError(self._error_message(exc)) from exc
        except (error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise AIProviderError(f"Gemini model discovery failed: {exc}") from exc
        return sorted(
            str(item.get("name") or "").removeprefix("models/")
            for item in data.get("models") or []
            if isinstance(item, dict) and item.get("name")
        )

    def health_check(self) -> tuple[bool, str]:
        try:
            self.list_models()
            return True, "Gemini API reachable"
        except Exception as exc:
            return False, str(exc)
