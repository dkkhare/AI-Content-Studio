from __future__ import annotations

from .library import PromptLibrary
from .template import PromptTemplate


def create_builtin_library() -> PromptLibrary:
    library = PromptLibrary()
    prompts = [
        PromptTemplate(
            name="ocr_cleanup",
            version="1.0",
            description="Correct OCR text while preserving meaning and structure.",
            system_template="You are a careful OCR correction assistant. Preserve meaning, language, paragraph order, and punctuation style.",
            user_template="Clean the following {{language}} OCR text. Return only the corrected text.\n\n{{text}}",
            defaults={"language": "original-language"},
        ),
        PromptTemplate(
            name="translation",
            version="1.0",
            description="Translate text while preserving structure and meaning.",
            system_template="You are a professional translator. Preserve names, formatting, paragraph structure, and intended meaning.",
            user_template="Translate from {{source_language}} to {{target_language}}. Return only the translation.\n\n{{text}}",
            defaults={"source_language": "auto"},
        ),
        PromptTemplate(
            name="chapter_summary",
            version="1.0",
            system_template="Summarize faithfully without inventing facts not present in the source.",
            user_template="Summarize this chapter in {{language}} for {{audience}}.\n\n{{text}}",
            defaults={"language": "English", "audience": "general readers"},
        ),
        PromptTemplate(
            name="script_generation",
            version="1.0",
            system_template="Create an engaging spoken script grounded only in the supplied source material.",
            user_template="Create a {{tone}} script in {{language}} from the following source.\n\n{{text}}",
            defaults={"tone": "clear and engaging", "language": "English"},
        ),
        PromptTemplate(
            name="subtitle_generation",
            version="1.0",
            system_template="Create concise readable subtitles. Do not add information not present in the source.",
            user_template="Convert the following transcript into subtitle-ready lines in {{language}}.\n\n{{text}}",
            defaults={"language": "English"},
        ),
        PromptTemplate(
            name="metadata_generation",
            version="1.0",
            system_template="Generate accurate publishing metadata from the supplied content only.",
            user_template="Generate a title, short description, and keywords in {{language}} for this content.\n\n{{text}}",
            defaults={"language": "English"},
        ),
        PromptTemplate(
            name="content_rewrite",
            version="1.0",
            system_template="Rewrite while preserving factual meaning and essential details.",
            user_template="Rewrite the following in a {{tone}} tone for {{audience}}.\n\n{{text}}",
            defaults={"tone": "clear", "audience": "general readers"},
        ),
        PromptTemplate(
            name="narration_assistant",
            version="1.0",
            system_template="Prepare text for natural narration while preserving meaning and pronunciation cues.",
            user_template="Prepare this {{language}} text for natural spoken narration. Return only narration-ready text.\n\n{{text}}",
            defaults={"language": "original-language"},
        ),
    ]
    for prompt in prompts:
        library.register(prompt)
    return library
