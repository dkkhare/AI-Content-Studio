import re


class TextProcessor:

    def normalize(self, text):

        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def split_sentences(self, text):

        return re.split(
            r"(?<=[.!?।])\s+",
            text,
        )