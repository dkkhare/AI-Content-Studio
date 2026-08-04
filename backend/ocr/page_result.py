from dataclasses import dataclass


@dataclass
class OCRPageResult:

    page: int

    text: str

    confidence: float

    provider: str