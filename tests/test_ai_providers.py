from __future__ import annotations

import json
import unittest

from backend.ai import (
    AIManager,
    AIRequest,
    GeminiProvider,
    OllamaProvider,
    OpenAIProvider,
)


class FakeResponse:
    def __init__(self, payload=None, lines=None):
        self.payload = payload
        self.lines = list(lines or [])

    def read(self):
        return json.dumps(self.payload or {}).encode("utf-8")

    def __iter__(self):
        return iter(self.lines)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class OpenAIProviderTests(unittest.TestCase):
    def test_generate_models_and_stream(self):
        def opener(req, timeout=None):
            url = req.full_url
            if url.endswith("/models"):
                return FakeResponse({"data": [{"id": "gpt-test"}]})
            body = json.loads(req.data.decode("utf-8"))
            if body.get("stream"):
                return FakeResponse(
                    lines=[
                        b'data: {"type":"response.output_text.delta","delta":"Hel"}\n',
                        b'data: {"type":"response.output_text.delta","delta":"lo"}\n',
                        b'data: {"type":"response.completed","response":{"model":"gpt-test","usage":{"input_tokens":2,"output_tokens":1,"total_tokens":3}}}\n',
                    ]
                )
            return FakeResponse(
                {
                    "model": "gpt-test",
                    "output": [
                        {
                            "type": "message",
                            "content": [{"type": "output_text", "text": "Hello"}],
                        }
                    ],
                    "usage": {"input_tokens": 2, "output_tokens": 1, "total_tokens": 3},
                }
            )

        provider = OpenAIProvider(api_key="test", opener=opener)
        response = provider.generate(AIRequest.from_prompt("Hi", model="gpt-test"))
        self.assertEqual(response.text, "Hello")
        self.assertEqual(response.usage.total_tokens, 3)
        self.assertEqual(provider.list_models(), ["gpt-test"])
        chunks = list(provider.stream(AIRequest.from_prompt("Hi", model="gpt-test")))
        self.assertEqual("".join(chunk.text for chunk in chunks), "Hello")
        self.assertTrue(chunks[-1].done)
        self.assertEqual(chunks[-1].usage.total_tokens, 3)


class OllamaProviderTests(unittest.TestCase):
    def test_generate_models_and_stream(self):
        def opener(req, timeout=None):
            if req.full_url.endswith("/api/tags"):
                return FakeResponse({"models": [{"model": "llama-test"}]})
            body = json.loads(req.data.decode("utf-8"))
            if body.get("stream"):
                return FakeResponse(
                    lines=[
                        b'{"model":"llama-test","message":{"content":"Hi"},"done":false}\n',
                        b'{"model":"llama-test","message":{"content":"!"},"done":true,"prompt_eval_count":4,"eval_count":2}\n',
                    ]
                )
            return FakeResponse(
                {
                    "model": "llama-test",
                    "message": {"role": "assistant", "content": "Hi!"},
                    "done": True,
                    "prompt_eval_count": 4,
                    "eval_count": 2,
                }
            )

        provider = OllamaProvider(default_model="llama-test", opener=opener)
        response = provider.generate(AIRequest.from_prompt("Hello"))
        self.assertEqual(response.text, "Hi!")
        self.assertEqual(response.usage.total_tokens, 6)
        self.assertEqual(provider.list_models(), ["llama-test"])
        chunks = list(provider.stream(AIRequest.from_prompt("Hello")))
        self.assertEqual("".join(chunk.text for chunk in chunks), "Hi!")
        self.assertTrue(chunks[-1].done)
        self.assertEqual(chunks[-1].usage.total_tokens, 6)


class GeminiProviderTests(unittest.TestCase):
    def test_generate_models_and_stream(self):
        def opener(req, timeout=None):
            url = req.full_url
            if "/models?" in url:
                return FakeResponse({"models": [{"name": "models/gemini-test"}]})
            if ":streamGenerateContent?" in url:
                return FakeResponse(
                    lines=[
                        b'data: {"candidates":[{"content":{"parts":[{"text":"Gem"}]}}]}\n',
                        b'data: {"candidates":[{"content":{"parts":[{"text":"ini"}]}}],"usageMetadata":{"promptTokenCount":3,"candidatesTokenCount":2,"totalTokenCount":5}}\n',
                    ]
                )
            return FakeResponse(
                {
                    "candidates": [
                        {"content": {"parts": [{"text": "Gemini"}]}}
                    ],
                    "usageMetadata": {
                        "promptTokenCount": 3,
                        "candidatesTokenCount": 2,
                        "totalTokenCount": 5,
                    },
                }
            )

        provider = GeminiProvider(
            api_key="test",
            default_model="gemini-test",
            opener=opener,
        )
        response = provider.generate(AIRequest.from_prompt("Hello"))
        self.assertEqual(response.text, "Gemini")
        self.assertEqual(response.usage.total_tokens, 5)
        self.assertEqual(provider.list_models(), ["gemini-test"])
        chunks = list(provider.stream(AIRequest.from_prompt("Hello")))
        self.assertEqual("".join(chunk.text for chunk in chunks), "Gemini")
        self.assertTrue(chunks[-1].done)
        self.assertEqual(chunks[-1].usage.total_tokens, 5)


class BuiltinRegistryTests(unittest.TestCase):
    def test_default_manager_registers_all_builtin_providers(self):
        manager = AIManager()
        self.assertEqual(manager.providers(), ["gemini", "ollama", "openai"])
        self.assertIn("streaming", manager.capabilities("openai"))
        self.assertIn("local", manager.capabilities("ollama"))


if __name__ == "__main__":
    unittest.main()
