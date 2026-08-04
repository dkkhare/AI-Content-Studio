import re


class TextSegmenter:

    MAX_LENGTH = 250

    def split(self, text):

        sentences = re.split(
            r'(?<=[.!?।])\s+',
            text
        )

        chunks = []

        current = ""

        for sentence in sentences:

            if len(current) + len(sentence) < self.MAX_LENGTH:

                current += sentence + " "

            else:

                chunks.append(current.strip())

                current = sentence

        if current:

            chunks.append(current.strip())

        return chunks