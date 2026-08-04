import re


class ChapterDetector:
    """
    Detects chapter headings such as:

    Chapter 1
    अध्याय 1
    Part I
    """

    PATTERNS = [
        r"^chapter\s+\d+",
        r"^part\s+[ivxlcdm]+",
        r"^अध्याय\s+\d+",
    ]

    def is_chapter(self, line):

        line = line.strip().lower()

        for pattern in self.PATTERNS:

            if re.match(pattern, line):

                return True

        return False