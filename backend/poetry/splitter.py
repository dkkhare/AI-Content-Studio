from backend.poetry.models import (
    Poem,
    Verse,
    Stanza,
)


class PoetrySplitter:

    def split(self, text):

        poems = []

        blocks = text.split("\n\n")

        poem = Poem(
            id=1,
            title="Untitled",
            language="Unknown",
            author=""
        )

        stanza = Stanza(number=1)

        verse_no = 1

        for line in blocks:

            if not line.strip():
                continue

            stanza.verses.append(
                Verse(
                    verse_no,
                    line.strip()
                )
            )

            verse_no += 1

        poem.stanzas.append(stanza)

        poems.append(poem)

        return poems