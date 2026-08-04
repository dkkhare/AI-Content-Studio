import re


class SentenceSplitter:
    """
    Splits text into sentences while preserving poetry structure.
    """

    SENTENCE_END = re.compile(
        r'(?<=[.!?])\s+'
    )

    def split(
        self,
        text,
    ):

        paragraphs = text.split("\n\n")

        sentences = []

        for paragraph in paragraphs:

            paragraph = paragraph.strip()

            if not paragraph:

                continue

            if "\n" in paragraph:

                lines = [

                    line.strip()

                    for line in paragraph.splitlines()

                    if line.strip()

                ]

                sentences.extend(lines)

            else:

                parts = self.SENTENCE_END.split(
                    paragraph
                )

                for part in parts:

                    part = part.strip()

                    if part:

                        sentences.append(part)

        return sentences