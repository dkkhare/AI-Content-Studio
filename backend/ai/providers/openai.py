from __future__ import annotations

import json
import os
from collections.abc import Iterable
from urllib import error, request

from ..exceptions import AIConfigurationError, AIProviderError
from ..models import AIRequest, AIResponse, AIStreamChunk, AIUsage
from ..provider import AIProvider


class OpenAIProvider(AIProvider):
    """OpenAI Responses API adapter using only the Python standard library."""

    provider_id = "openai"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        api_key_env: str = "OPENAI_API_KEY",
        base_url: str | None = None,
        timeout: float = 60.0,
        opener=None,
    ):
        self.api_key_env = api_key_env
        self.api_key = api_key or os.getenv(api_key_env, "")
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.timeout = max(1.0, float(timeout))
        self._open = opener or request.urlopen

    def configured(self) -> bool:
        return bool(self.api_key)

    def capabilities(self) -> set[str]:
        return {"text", "streaming", "models"}

    def _headers(self) -> dict[str, str]:
        if not self.configured():
            raise AIConfigurationError(
                f"OpenAI API key is missing. Set environment variable {self.api_key_env}."
            )
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _payload(self, value: AIRequest, *, stream: bool = False) -> dict:
        if not value.model:
            raise AIConfigurationError("OpenAI request requires a model.")
        payload: dict = {
            "model": value.model,
            "input": [
                {"role": message.role, "content": message.content}
                for message in value.messages
            ],
        }
        if value.temperature is not None:
            payload["temperature"] = float(value.temperature)
        if value.max_output_tokens is not None:
            payload["max_output_tokens"] = int(value.max_output_tokens)
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def _usage(data: dict | None) -> AIUsage:
        raw = (data or {}).get("usage") or {}
        return AIUsage(
            input_tokens=int(raw.get("input_tokens") or 0),
            output_tokens=int(raw.get("output_tokens") or 0),
            total_tokens=int(raw.get("total_tokens") or 0),
        )

    @staticmethod
    def _text(data: dict) -> str:
        direct = data.get("output_text")
        if isinstance(direct, str):
            return direct
        parts: list[str] = []
        for item in data.get("output") or []:
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            for content in item.get("content") or []:
                if isinstance(content, dict) and content.get("type") == "output_text":
                    parts.append(str(content.get("text") or ""))
        return "".join(parts)

    @staticmethod
    def _error_message(exc: error.HTTPError) -> str:
        try:
            data = json.loads(exc.read().decode("utf-8"))
            detail = str((data.get("error") or {}).get("message") or "").strip()
        except Exception:
            detail = ""
        return f"OpenAI HTTP {exc.code}" + (f": {detail}" if detail else "")

    def generate(self, value: AIRequest) -> AIResponse:
        req = request.Request(
            f"{self.base_url}/responses",
            data=json.dumps(self._payload(value)).encode("utf-8"),
            headers=self._headers(),
            method="POST",
        )
        try:
            with self._open(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            raise AIProviderError(self._error_message(exc)) from exc
        except (error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise AIProviderError(f"OpenAI request failed: {exc}") from exc

        return AIResponse(
            text=self._text(data),
            provider=self.provider_id,
            model=str(data.get("model") or value.model),
            usage=self._usage(data),
            raw=data,
        )

    def stream(self, value: AIRequest) -> Iterable[AIStreamChunk]:
        req = request.Request(
            f"{self.base_url}/responses",
            data=json.dumps(self._payload(value, stream=True)).encode("utf-8"),
            headers={**self._headers(), "Accept": "text/event-stream"},
            method="POST",
        )
        try:
            with self._open(req, timeout=self.timeout) as response:
                for raw_line in response:
                    line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else str(raw_line)
                    line = line.strip()
                    if not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if not payload or payload == "[DONE]":
                        continue
                    try:
                        event = json.loads(payload)
                    except json.JSONDecodeError:
                        continue
                    event_type = str(event.get("type") or "")
                    if event_type == "response.output_text.delta":
                        delta = str(event.get("delta") or "")
                        if delta:
                            yield AIStreamChunk(
                                text=delta,
                                provider=self.provider_id,
                                model=value.model,
                                raw=event,
                            )
                    elif event_type in {"response.completed", "response.done"}:
                        response_data = event.get("response") or event
                        yield AIStreamChunk(
                            provider=self.provider_id,
                            model=str(response_data.get("model") or value.model),
                            done=True,
                            usage=self._usage(response_data),
                            raw=event,
                        )
        except error.HTTPError as exc:
            raise AIProviderError(self._error_message(exc)) from exc
        except (error.URLError, TimeoutError, OSError) as exc:
            raise AIProviderError(f"OpenAI streaming request failed: {exc}") from exc

    def list_models(self) -> list[str]:
        req = request.Request(
            f"{self.base_url}/models",
            headers=self._headers(),
            method="GET",
        )
        try:
            with self._open(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            raise AIProviderError(self._error_message(exc)) from exc
        except (error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise AIProviderError(f"OpenAI model discovery failed: {exc}") from exc
        return sorted(
            str(item.get("id"))
            for item in data.get("data") or []
            if isinstance(item, dict) and item.get("id")
        )

    def health_check(self) -> tuple[bool, str]:
        try:
            self.list_models()
            return True, "OpenAI API reachable"
        except Exception as exc:
            return False, str(exc)
