class DuplicateDetector:

    def remove_duplicate_lines(self, lines):

        result = []

        seen = set()

        for line in lines:

            key = line.strip()

            if not key:

                continue

            if key in seen:

                continue

            seen.add(key)

            result.append(line)

        return result