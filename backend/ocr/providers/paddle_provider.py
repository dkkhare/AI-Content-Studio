from backend.ocr.providers.base_provider import OCRProvider


class PaddleProvider(OCRProvider):

    def initialize(self):
        pass

    def recognize(self, image_path):
        raise NotImplementedError(
            "PaddleOCR integration will be implemented in Milestone 9."
        )