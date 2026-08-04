import fitz


class OCRDetector:

    def needs_ocr(
        self,
        page,
    ):

        text = page.get_text()

        return len(text.strip()) == 0