from __future__ import annotations

import unittest

from backend.ai import AIConfig, AIManager, AIProvider, AIProviderRegistry, AIRequest, AIResponse, AIStreamChunk, AIUsage
from backend.ai.prompts import PromptLibrary, PromptRenderError, PromptTemplate, create_builtin_library


class EchoProvider(AIProvider):
    provider_id = "echo"

    def configured(self) -> bool:
        return True

    def generate(self, request: AIRequest) -> AIResponse:
        text = request.messages[-1].content
        return AIResponse(text=text, provider="echo", model=request.model or "echo-model", usage=AIUsage(1, 1))

    def stream(self, request: AIRequest):
        text = request.messages[-1].content
        yield AIStreamChunk(text=text, provider="echo", model="echo-model", done=True, usage=AIUsage(1, 1))


class PromptFrameworkTests(unittest.TestCase):
    def test_template_renders_required_and_default_variables(self):
        template = PromptTemplate(
            name="demo",
            version="1.0",
            system_template="Language: {{language}}",
            user_template="Hello {{name}}",
            defaults={"language": "Hindi"},
        )
        request = template.render({"name": "Dev"})
        self.assertEqual(request.messages[0].content, "Language: Hindi")
        self.assertEqual(request.messages[1].content, "Hello Dev")

    def test_template_reports_missing_variables(self):
        template = PromptTemplate(name="demo", version="1.0", user_template="{{text}} {{language}}")
        with self.assertRaises(PromptRenderError):
            template.render({"text": "hello"})

    def test_library_selects_latest_prompt_version(self):
        library = PromptLibrary()
        library.register(PromptTemplate("demo", "1.0", "one"))
        library.register(PromptTemplate("demo", "2.0", "two"))
        self.assertEqual(library.get("demo").version, "2.0")
        self.assertEqual(library.get("demo", "1.0").user_template, "one")

    def test_builtin_catalog_contains_expected_prompts(self):
        names = create_builtin_library().names()
        for name in (
            "ocr_cleanup",
            "hindi_spelling_correction",
            "hindi_grammar_correction",
            "translation",
            "chapter_summary",
            "script_generation",
            "subtitle_generation",
            "metadata_generation",
            "content_rewrite",
            "narration_assistant",
        ):
            self.assertIn(name, names)

    def test_hindi_proofing_prompts_are_independent(self):
        library = create_builtin_library()
        spelling = library.get("hindi_spelling_correction")
        grammar = library.get("hindi_grammar_correction")

        spelling_request = spelling.render({"text": "हिन्दी पाठ"})
        grammar_request = grammar.render({"text": "हिन्दी पाठ"})

        self.assertIn("spelling", spelling_request.messages[0].content.lower())
        self.assertIn("do not rewrite sentences", spelling_request.messages[0].content.lower())
        self.assertIn("grammar", grammar_request.messages[0].content.lower())
        self.assertIn("do not summarize", grammar_request.messages[0].content.lower())

    def test_manager_executes_and_streams_prompt(self):
        registry = AIProviderRegistry()
        registry.register("echo", EchoProvider)
        manager = AIManager(registry=registry, config=AIConfig(default_provider="echo"))
        response = manager.execute_prompt(
            "translation",
            {"text": "Namaste", "target_language": "English"},
        )
        self.assertIn("Namaste", response.text)
        chunks = list(
            manager.stream_prompt(
                "ocr_cleanup",
                {"text": "abc", "language": "English"},
            )
        )
        self.assertTrue(chunks[-1].done)
        self.assertIn("abc", chunks[-1].text)


if __name__ == "__main__":
    unittest.main()
