import pytesseract

from backend.ocr.base import OCREngine
from backend.ocr.result import OCRResult


class TesseractEngine(OCREngine):

    def __init__(self, language="eng"):

        self.language = language

    def recognize(self, image, page_number):

        text = pytesseract.image_to_string(
            image,
            lang=self.language,
        )

        return OCRResult(
            page_number=page_number,
            text=text,
            confidence=100.0,
        )