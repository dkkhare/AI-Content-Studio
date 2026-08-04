from backend.ocr.providers.base_provider import OCRProvider


class TesseractProvider(OCRProvider):

    def initialize(self):
        pass

    def recognize(self, image_path):
        raise NotImplementedError(
            "TesseractOCR integration will be implemented in Milestone 9."
        )