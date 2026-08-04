import re


class TextCleaner:

    def clean(self, text: str) -> str:

        # Remove multiple blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove page numbers
        text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)

        # Remove extra spaces
        text = re.sub(r"[ \t]+", " ", text)

        return text.strip()