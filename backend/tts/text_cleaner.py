import re


class TextCleaner:
    """
    Cleans text before sending it to the TTS engine.
    """

    def __init__(self):

        self.multiple_spaces = re.compile(r"[ \t]+")

        self.multiple_blank_lines = re.compile(r"\n{3,}")

    def clean(
        self,
        text,
        preserve_stanzas=True,
    ):

        if not text:

            return ""

        text = text.replace("\r\n", "\n")

        text = text.replace("\r", "\n")

        text = text.replace("\t", " ")

        text = self.multiple_spaces.sub(
            " ",
            text,
        )

        if preserve_stanzas:

            text = self.multiple_blank_lines.sub(
                "\n\n",
                text,
            )

        else:

            text = text.replace("\n", " ")

        return text.strip()

    def remove_control_characters(
        self,
        text,
    ):

        return "".join(

            ch

            for ch in text

            if ch.isprintable()

            or ch in "\n\t"

        )

    def normalize_quotes(
        self,
        text,
    ):

        replacements = {

            "“": '"',

            "”": '"',

            "‘": "'",

            "’": "'",

        }

        for old, new in replacements.items():

            text = text.replace(old, new)

        return text