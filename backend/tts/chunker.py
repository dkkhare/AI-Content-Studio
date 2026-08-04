class TextChunker:
    """
    Converts sentences into chunks suitable
    for long-form TTS generation.
    """

    def __init__(
        self,
        max_length=180,
        overlap=1,
    ):

        self.max_length = max_length

        self.overlap = overlap

    def chunk(
        self,
        sentences,
    ):

        chunks = []

        current = ""

        for sentence in sentences:

            if len(current) + len(sentence) + 1 <= self.max_length:

                if current:

                    current += " "

                current += sentence

            else:

                if current:

                    chunks.append(current)

                current = sentence

        if current:

            chunks.append(current)

        if self.overlap <= 0:

            return chunks

        overlapped = []

        for index, chunk in enumerate(chunks):

            if index == 0:

                overlapped.append(chunk)

                continue

            previous = chunks[index - 1]

            overlap_text = previous.split()

            overlap_text = overlap_text[-15:]

            overlap_text = " ".join(overlap_text)

            overlapped.append(

                overlap_text + " " + chunk

            )

        return overlapped