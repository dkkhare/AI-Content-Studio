from abc import ABC, abstractmethod

from backend.ocr.result import OCRResult


class OCREngine(ABC):

    @abstractmethod
    def recognize(self, image, page_number: int) -> OCRResult:
        """
        Perform OCR on one page.
        """
        pass