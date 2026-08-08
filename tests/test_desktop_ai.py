from __future__ import annotations

import os
import unittest

from backend.ai import AIResponse, AIStreamChunk
from desktop.ai.configuration import AIProfile, AISettingsStore
from desktop.controllers.ai_controller import AIDesktopController


class MemorySettings:
    def __init__(self):
        self.data = {}
        self.synced = False

    def value(self, key, default=None):
        return self.data.get(key, default)

    def set_value(self, key, value):
        self.data[key] = value

    def sync(self):
        self.synced = True


class FakeManager:
    def __init__(self):
        self.config = None
        self.requests = []

    def providers(self):
        return ["gemini", "ollama", "openai"]

    def list_prompts(self):
        return ["hindi_spelling_correction", "translation"]

    def health_check(self, provider):
        return True, f"{provider} reachable"

    def list_models(self, provider):
        return [f"{provider}-model"]

    def generate(self, request, provider_id=None):
        self.requests.append((request, provider_id))
        return AIResponse("done", provider_id, request.model)

    def stream_prompt(self, template, variables, provider_id=None, model=""):
        self.requests.append((template, variables, provider_id, model))
        yield AIStreamChunk("corrected", provider_id, model, done=True)

    def stream(self, request, provider_id=None):
        self.requests.append((request, provider_id))
        yield AIStreamChunk("one", provider_id, request.model)
        yield AIStreamChunk("two", provider_id, request.model, done=True)


class DesktopAIConfigurationTests(unittest.TestCase):
    def tearDown(self):
        os.environ.pop("OPENAI_API_KEY", None)
        os.environ.pop("GEMINI_API_KEY", None)

    def test_non_secret_profile_round_trip(self):
        settings = MemorySettings()
        store = AISettingsStore(settings)
        expected = AIProfile("openai", "gpt-test", ["gemini", "openai"], 45)
        saved = store.save(expected)
        loaded = store.load()
        self.assertEqual(saved.provider, "openai")
        self.assertEqual(loaded.model, "gpt-test")
        self.assertEqual(loaded.failover, ["gemini"])
        self.assertEqual(loaded.timeout_seconds, 45)
        self.assertTrue(settings.synced)
        self.assertNotIn("api_key", " ".join(settings.data))

    def test_secret_is_session_only(self):
        settings = MemorySettings()
        store = AISettingsStore(settings)
        store.set_session_secret("openai", "secret-value")
        self.assertEqual(os.environ["OPENAI_API_KEY"], "secret-value")
        self.assertTrue(store.has_session_secret("openai"))
        self.assertEqual(settings.data, {})

    def test_invalid_provider_is_rejected(self):
        with self.assertRaises(ValueError):
            AIProfile("unknown").normalized()


class DesktopAIControllerTests(unittest.TestCase):
    def test_configure_health_models_and_generate(self):
        manager = FakeManager()
        controller = AIDesktopController(manager)
        profile = controller.configure(AIProfile("ollama", "qwen-test"))
        self.assertEqual(profile.provider, "ollama")
        self.assertEqual(manager.config.default_model, "qwen-test")
        self.assertEqual(controller.health_check("ollama"), (True, "ollama reachable"))
        self.assertEqual(controller.discover_models("ollama"), ["ollama-model"])
        self.assertEqual(
            controller.generate("hello", provider="ollama", model="qwen-test"),
            "done",
        )
        self.assertEqual(manager.requests[0][0].model, "qwen-test")

    def test_template_defaults_and_streaming(self):
        manager = FakeManager()
        controller = AIDesktopController(manager)
        self.assertEqual(
            controller.prompt_variables("translation", "hello")["target_language"],
            "Hindi",
        )
        chunks = list(controller.stream_prompt(
            "translation",
            "hello",
            provider="gemini",
            model="gemini-test",
        ))
        self.assertEqual(chunks[0].text, "corrected")
        self.assertEqual(manager.requests[0][1]["text"], "hello")

    def test_empty_prompt_and_stream_cancellation(self):
        controller = AIDesktopController(FakeManager())
        with self.assertRaises(ValueError):
            controller.generate(" ", provider="ollama", model="qwen")

        stream = controller.stream("hello", provider="ollama", model="qwen")
        self.assertEqual(next(stream).text, "one")
        controller.cancel()
        with self.assertRaises(StopIteration):
            next(stream)
        self.assertTrue(controller.cancelled)


if __name__ == "__main__":
    unittest.main()
