from __future__ import annotations

import unittest

from backend.ai import (
    AIConfig,
    AIManager,
    AIProvider,
    AIProviderRegistry,
    AIRequest,
    AIResponse,
    AIStreamChunk,
    AIStreamInterruptedError,
)


class CapturingProvider(AIProvider):
    def __init__(self, provider_id, *, chunks=None, fail=False):
        self.provider_id = provider_id
        self.requests = []
        self.chunks = chunks
        self.fail = fail

    def configured(self):
        return True

    def generate(self, request):
        self.requests.append(request)
        if self.fail:
            raise RuntimeError("failed")
        return AIResponse("ok", self.provider_id, request.model)

    def stream(self, request):
        self.requests.append(request)
        if self.chunks is not None:
            yield from self.chunks
            return
        if self.fail:
            raise RuntimeError("failed")
        yield AIStreamChunk("ok", self.provider_id, request.model, done=True)


class AIHardeningTests(unittest.TestCase):
    def test_request_is_not_mutated_and_model_is_provider_specific(self):
        provider = CapturingProvider("openai")
        registry = AIProviderRegistry()
        registry.register("openai", lambda: provider)
        manager = AIManager(
            registry=registry,
            config=AIConfig(
                default_provider="openai",
                default_model="fallback",
                provider_models={"openai": "gpt-test"},
            ),
        )
        request = AIRequest.from_prompt("hello", metadata={"source": "test"})
        manager.generate(request)
        self.assertEqual(request.model, "")
        self.assertEqual(provider.requests[0].model, "gpt-test")
        self.assertIsNot(provider.requests[0], request)
        self.assertIsNot(provider.requests[0].metadata, request.metadata)

    def test_provider_chain_is_normalized_and_deduplicated(self):
        provider = CapturingProvider("good")
        registry = AIProviderRegistry()
        registry.register("good", lambda: provider)
        manager = AIManager(
            registry=registry,
            config=AIConfig(default_provider="GOOD", provider_order=["good", " GOOD "]),
        )
        self.assertEqual(manager._provider_chain(), ["good"])

    def test_stream_falls_back_before_any_output(self):
        bad = CapturingProvider("bad", fail=True)
        good = CapturingProvider("good")
        registry = AIProviderRegistry()
        registry.register("bad", lambda: bad)
        registry.register("good", lambda: good)
        manager = AIManager(
            registry=registry,
            config=AIConfig(default_provider="bad", provider_order=["good"]),
        )
        self.assertEqual("".join(chunk.text for chunk in manager.stream(AIRequest.from_prompt("x"))), "ok")

    def test_stream_never_mixes_providers_after_partial_output(self):
        def interrupted():
            yield AIStreamChunk("partial", "bad")
            raise RuntimeError("connection lost")

        bad = CapturingProvider("bad", chunks=interrupted())
        good = CapturingProvider("good")
        registry = AIProviderRegistry()
        registry.register("bad", lambda: bad)
        registry.register("good", lambda: good)
        manager = AIManager(
            registry=registry,
            config=AIConfig(default_provider="bad", provider_order=["good"]),
        )
        stream = manager.stream(AIRequest.from_prompt("x"))
        self.assertEqual(next(stream).text, "partial")
        with self.assertRaises(AIStreamInterruptedError):
            next(stream)
        self.assertEqual(good.requests, [])


if __name__ == "__main__":
    unittest.main()
