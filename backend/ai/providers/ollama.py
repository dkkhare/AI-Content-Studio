from __future__ import annotations

import json
import os
from collections.abc import Iterable
from urllib import error, request

from ..exceptions import AIConfigurationError, AIProviderError
from ..models import AIRequest, AIResponse, AIStreamChunk, AIUsage
from ..provider import AIProvider


class OllamaProvider(AIProvider):
    """Local Ollama chat adapter using the documented HTTP API."""

    provider_id = "ollama"

    def __init__(
        self,
        *,
        base_url: str | None = None,
        default_model: str | None = None,
        timeout: float = 120.0,
        opener=None,
    ):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.default_model = default_model or os.getenv("OLLAMA_MODEL", "")
        self.timeout = max(1.0, float(timeout))
        self._open = opener or request.urlopen

    def configured(self) -> bool:
        return bool(self.base_url)

    def capabilities(self) -> set[str]:
        return {"text", "streaming", "models", "local"}

    def _model(self, value: AIRequest) -> str:
        model = value.model or self.default_model
        if not model:
            raise AIConfigurationError("Ollama request requires a model. Set OLLAMA_MODEL or request.model.")
        return model

    def _payload(self, value: AIRequest, *, stream: bool) -> dict:
        payload: dict = {
            "model": self._model(value),
            "messages": [
                {"role": message.role, "content": message.content}
                for message in value.messages
            ],
            "stream": bool(stream),
        }
        options: dict = {}
        if value.temperature is not None:
            options["temperature"] = float(value.temperature)
        if value.max_output_tokens is not None:
            options["num_predict"] = int(value.max_output_tokens)
        if options:
            payload["options"] = options
        return payload

    @staticmethod
    def _usage(data: dict) -> AIUsage:
        input_tokens = int(data.get("prompt_eval_count") or 0)
        output_tokens = int(data.get("eval_count") or 0)
        return AIUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )

    def generate(self, value: AIRequest) -> AIResponse:
        req = request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(self._payload(value, stream=False)).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self._open(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            raise AIProviderError(f"Ollama HTTP {exc.code}") from exc
        except (error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise AIProviderError(f"Ollama request failed: {exc}") from exc

        message = data.get("message") or {}
        return AIResponse(
            text=str(message.get("content") or ""),
            provider=self.provider_id,
            model=str(data.get("model") or self._model(value)),
            usage=self._usage(data),
            raw=data,
        )

    def stream(self, value: AIRequest) -> Iterable[AIStreamChunk]:
        req = request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(self._payload(value, stream=True)).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self._open(req, timeout=self.timeout) as response:
                for raw_line in response:
                    line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else str(raw_line)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    message = data.get("message") or {}
                    text = str(message.get("content") or "")
                    done = bool(data.get("done"))
                    yield AIStreamChunk(
                        text=text,
                        provider=self.provider_id,
                        model=str(data.get("model") or self._model(value)),
                        done=done,
                        usage=self._usage(data) if done else None,
                        raw=data,
                    )
        except error.HTTPError as exc:
            raise AIProviderError(f"Ollama HTTP {exc.code}") from exc
        except (error.URLError, TimeoutError, OSError) as exc:
            raise AIProviderError(f"Ollama streaming request failed: {exc}") from exc

    def list_models(self) -> list[str]:
        req = request.Request(f"{self.base_url}/api/tags", method="GET")
        try:
            with self._open(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            raise AIProviderError(f"Ollama HTTP {exc.code}") from exc
        except (error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise AIProviderError(f"Ollama model discovery failed: {exc}") from exc
        return sorted(
            str(item.get("model") or item.get("name"))
            for item in data.get("models") or []
            if isinstance(item, dict) and (item.get("model") or item.get("name"))
        )

    def health_check(self) -> tuple[bool, str]:
        try:
            self.list_models()
            return True, "Ollama server reachable"
        except Exception as exc:
            return False, str(exc)
