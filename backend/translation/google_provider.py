from __future__ import annotations

import html
import json
import os
import time
from urllib import error, parse, request

from .base import TranslationProvider, TranslationProviderError


class GoogleTranslationProvider(TranslationProvider):
    """Google Cloud Translation Basic (v2) provider using the stdlib HTTP client."""

    provider_id = "google"
    endpoint = "https://translation.googleapis.com/language/translate/v2"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        api_key_env: str = "GOOGLE_TRANSLATE_API_KEY",
        timeout: float = 30.0,
        retries: int = 2,
    ):
        self.api_key_env = api_key_env
        self.api_key = api_key or os.getenv(api_key_env, "")
        self.timeout = max(1.0, float(timeout))
        self.retries = max(0, int(retries))

    def configured(self) -> bool:
        return bool(self.api_key)

    def translate(
        self,
        text: str,
        *,
        source_language: str | None = None,
        target_language: str | None = None,
    ) -> str:
        value = str(text or "")
        if not value:
            return ""
        if not target_language:
            raise TranslationProviderError("Google translation requires a target language.")
        if not self.configured():
            raise TranslationProviderError(
                f"Google translation API key is missing. Set environment variable {self.api_key_env}."
            )

        payload = {
            "q": value,
            "target": str(target_language),
            "format": "text",
        }
        if source_language:
            payload["source"] = str(source_language)

        url = f"{self.endpoint}?{parse.urlencode({'key': self.api_key})}"
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                with request.urlopen(req, timeout=self.timeout) as response:
                    data = json.loads(response.read().decode("utf-8"))
                translations = data.get("data", {}).get("translations", [])
                if not translations:
                    raise TranslationProviderError("Google translation returned no translation result.")
                translated = translations[0].get("translatedText", "")
                return html.unescape(str(translated))
            except error.HTTPError as exc:
                last_error = TranslationProviderError(self._http_error_message(exc))
                if exc.code < 500 and exc.code != 429:
                    break
            except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = TranslationProviderError(f"Google translation request failed: {exc}")
            except TranslationProviderError as exc:
                last_error = exc
                break

            if attempt < self.retries:
                time.sleep(min(4.0, 0.5 * (2**attempt)))

        raise last_error or TranslationProviderError("Google translation failed.")

    @staticmethod
    def _http_error_message(exc: error.HTTPError) -> str:
        detail = ""
        try:
            payload = json.loads(exc.read().decode("utf-8"))
            detail = str(payload.get("error", {}).get("message", "")).strip()
        except Exception:
            detail = ""
        suffix = f": {detail}" if detail else ""
        return f"Google translation HTTP {exc.code}{suffix}"
