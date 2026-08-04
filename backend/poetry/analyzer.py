from backend.poetry.cleaner import TextCleaner
from backend.poetry.language_detector import LanguageDetector
from backend.poetry.splitter import PoetrySplitter


class PoetryAnalyzer:

    def analyze(self, text):

        cleaned = TextCleaner().clean(text)

        poems = PoetrySplitter().split(cleaned)

        detector = LanguageDetector()

        for poem in poems:

            combined = ""

            for stanza in poem.stanzas:

                for verse in stanza.verses:

                    combined += verse.text + "\n"

            poem.language = detector.detect(combined)

        return poems