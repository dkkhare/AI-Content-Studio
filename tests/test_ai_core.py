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
    AIUsage,
    AIUsageTracker,
    collect_stream,
)


class MockProvider(AIProvider):
    provider_id = "mock"

    def __init__(self, *, configured=True, fail=False):
        self._configured = configured
        self.fail = fail

    def configured(self) -> bool:
        return self._configured

    def generate(self, request: AIRequest) -> AIResponse:
        if self.fail:
            raise RuntimeError("mock failure")
        return AIResponse(
            text="ok",
            provider=self.provider_id,
            model=request.model or "mock-model",
            usage=AIUsage(input_tokens=3, output_tokens=2),
        )

    def stream(self, request: AIRequest):
        yield AIStreamChunk(text="o", provider=self.provider_id, model="mock-model")
        yield AIStreamChunk(
            text="k",
            provider=self.provider_id,
            model="mock-model",
            done=True,
            usage=AIUsage(input_tokens=3, output_tokens=2),
        )


class AICoreTests(unittest.TestCase):
    def test_registry_and_manager_generate(self):
        registry = AIProviderRegistry()
        registry.register("mock", MockProvider)
        manager = AIManager(
            registry=registry,
            config=AIConfig(default_provider="mock", default_model="default-model"),
        )
        response = manager.generate(AIRequest.from_prompt("hello"))
        self.assertEqual(response.text, "ok")
        self.assertEqual(response.model, "default-model")
        self.assertEqual(manager.usage.totals.total_tokens, 5)

    def test_manager_failover(self):
        registry = AIProviderRegistry()
        registry.register("bad", lambda: MockProvider(fail=True))
        registry.register("good", MockProvider)
        config = AIConfig(default_provider="bad", provider_order=["good"])
        manager = AIManager(registry=registry, config=config)
        response = manager.generate(AIRequest.from_prompt("hello"))
        self.assertEqual(response.provider, "mock")
        self.assertEqual(response.text, "ok")

    def test_streaming_and_usage(self):
        registry = AIProviderRegistry()
        registry.register("mock", MockProvider)
        manager = AIManager(registry=registry, config=AIConfig(default_provider="mock"))
        text = collect_stream(manager.stream(AIRequest.from_prompt("hello")))
        self.assertEqual(text, "ok")
        self.assertEqual(manager.usage.totals.total_tokens, 5)

    def test_usage_tracker_snapshot(self):
        tracker = AIUsageTracker()
        tracker.record("provider", "model", AIUsage(input_tokens=4, output_tokens=6))
        snapshot = tracker.snapshot()
        self.assertEqual(snapshot["totals"]["total_tokens"], 10)
        self.assertEqual(snapshot["by_provider"]["provider"]["input_tokens"], 4)


if __name__ == "__main__":
    unittest.main()
