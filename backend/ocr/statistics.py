from dataclasses import dataclass


@dataclass
class OCRStatistics:

    processed: int = 0

    skipped: int = 0

    recognized: int = 0

    failed: int = 0