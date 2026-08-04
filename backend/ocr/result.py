from dataclasses import dataclass


@dataclass
class OCRResult:

    page_number: int

    text: str

    confidence: float