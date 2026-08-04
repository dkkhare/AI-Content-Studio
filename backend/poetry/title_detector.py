class TitleDetector:
    """
    Detects probable poem titles.

    Current heuristic:
    - First non-empty short line
    - Less than 80 characters
    """

    def detect(self, text: str) -> str:

        for line in text.splitlines():

            line = line.strip()

            if not line:
                continue

            if len(line) < 80:
                return line

        return "Untitled"