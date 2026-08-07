from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from backend.translation import GoogleTranslationProvider, TranslationProviderError


class _FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class GoogleTranslationProviderTests(unittest.TestCase):
    def test_missing_key_is_reported_without_network_call(self):
        provider = GoogleTranslationProvider(api_key="", api_key_env="ACS_MISSING_KEY")
        with patch.dict("os.environ", {}, clear=True):
            provider.api_key = ""
            with self.assertRaises(TranslationProviderError) as ctx:
                provider.translate("hello", target_language="hi")
        self.assertIn("ACS_MISSING_KEY", str(ctx.exception))

    def test_provider_parses_google_v2_translation_response(self):
        provider = GoogleTranslationProvider(api_key="test-key", retries=0)
        payload = {
            "data": {
                "translations": [
                    {"translatedText": "नमस्ते &amp; स्वागत"}
                ]
            }
        }
        with patch(
            "backend.translation.google_provider.request.urlopen",
            return_value=_FakeResponse(payload),
        ) as urlopen:
            result = provider.translate(
                "Hello & welcome",
                source_language="en",
                target_language="hi",
            )

        self.assertEqual(result, "नमस्ते & स्वागत")
        request_object = urlopen.call_args.args[0]
        self.assertIn("key=test-key", request_object.full_url)
        body = json.loads(request_object.data.decode("utf-8"))
        self.assertEqual(body["q"], "Hello & welcome")
        self.assertEqual(body["source"], "en")
        self.assertEqual(body["target"], "hi")
        self.assertEqual(body["format"], "text")

    def test_target_language_is_required(self):
        provider = GoogleTranslationProvider(api_key="test-key")
        with self.assertRaises(TranslationProviderError):
            provider.translate("hello")


if __name__ == "__main__":
    unittest.main()
