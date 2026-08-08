from __future__ import annotations

import argparse
import io
import json
import unittest

from backend.ai import AIResponse, AIStreamChunk, AIUsage
from scripts.ai_smoke import run


class FakeManager:
    def __init__(self, healthy=True):
        self.healthy = healthy
        self.calls = []

    def health_check(self, provider):
        return (self.healthy, "reachable" if self.healthy else "offline")

    def generate(self, request, *, provider_id=None):
        self.calls.append(("generate", provider_id, request.model))
        return AIResponse("AI Content Studio OK", provider_id, request.model, AIUsage(2, 3))

    def stream(self, request, *, provider_id=None):
        self.calls.append(("stream", provider_id, request.model))
        yield AIStreamChunk("AI Content ", provider_id, request.model)
        yield AIStreamChunk("Studio OK", provider_id, request.model, True, AIUsage(2, 3))

    def execute_prompt(self, name, variables, **kwargs):
        self.calls.append((name, variables["text"], kwargs["model"]))
        return AIResponse("सुधारा गया", kwargs["provider_id"], kwargs["model"], AIUsage(2, 3))


def args(**overrides):
    values = dict(
        provider="ollama",
        model="qwen-test",
        prompt="hello",
        stream=False,
        hindi_proof=False,
    )
    values.update(overrides)
    return argparse.Namespace(**values)


class AISmokeCLITests(unittest.TestCase):
    def test_generate_success_returns_json_and_zero(self):
        output = io.StringIO()
        code = run(args(), manager=FakeManager(), stdout=output)
        payload = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["usage"]["total_tokens"], 5)

    def test_health_failure_returns_two_without_generation(self):
        output = io.StringIO()
        manager = FakeManager(healthy=False)
        self.assertEqual(run(args(), manager=manager, stdout=output), 2)
        self.assertEqual(manager.calls, [])

    def test_stream_and_hindi_proof_paths(self):
        output = io.StringIO()
        manager = FakeManager()
        self.assertEqual(run(args(stream=True), manager=manager, stdout=output), 0)
        self.assertIn(("stream", "ollama", "qwen-test"), manager.calls)

        output = io.StringIO()
        manager = FakeManager()
        self.assertEqual(run(args(hindi_proof=True), manager=manager, stdout=output), 0)
        self.assertEqual(manager.calls[0][0], "hindi_spelling_correction")
        self.assertEqual(manager.calls[1][0], "hindi_grammar_correction")


if __name__ == "__main__":
    unittest.main()
