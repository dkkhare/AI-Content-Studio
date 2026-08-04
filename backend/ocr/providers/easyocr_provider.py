from backend.ocr.providers.base_provider import OCRProvider


class EasyocrProvider(OCRProvider):

    def initialize(self):
        pass

    def recognize(self, image_path):
        raise NotImplementedError(
            "EasyOCR integration will be implemented in Milestone 9."
        )