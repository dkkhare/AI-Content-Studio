class LanguageDetector:

    def detect(self, text: str):

        hindi = sum(
            1
            for c in text
            if "\u0900" <= c <= "\u097F"
        )

        english = sum(
            1
            for c in text
            if c.isascii() and c.isalpha()
        )

        if hindi > english:
            return "Hindi"

        return "English"