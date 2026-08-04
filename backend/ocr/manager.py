from typing import Dict, Optional

from backend.ocr.providers.base_provider import OCRProvider
from backend.ocr.providers.paddle_provider import PaddleProvider
from backend.ocr.providers.tesseract_provider import TesseractProvider
from backend.ocr.providers.easyocr_provider import EasyOCRProvider


class OCRManager:
    """
    Central manager for all OCR providers.

    Supported providers:
        - PaddleOCR
        - Tesseract
        - EasyOCR

    Future providers can be added by simply registering them.
    """

    def __init__(self):

        self.providers: Dict[str, OCRProvider] = {}

        self.active_provider: Optional[OCRProvider] = None

        self.register_provider(
            "paddle",
            PaddleProvider(),
        )

        self.register_provider(
            "tesseract",
            TesseractProvider(),
        )

        self.register_provider(
            "easyocr",
            EasyOCRProvider(),
        )

        self.set_provider("paddle")

    def register_provider(
        self,
        name: str,
        provider: OCRProvider,
    ):

        self.providers[name.lower()] = provider

    def available_providers(self):

        return list(self.providers.keys())

    def set_provider(
        self,
        name: str,
    ):

        name = name.lower()

        if name not in self.providers:

            raise ValueError(
                f"Unknown OCR provider: {name}"
            )

        self.active_provider = self.providers[name]

        self.active_provider.initialize()

    def get_provider_name(self):

        for name, provider in self.providers.items():

            if provider is self.active_provider:

                return name

        return None

    def recognize(
        self,
        image_path: str,
    ):

        if self.active_provider is None:

            raise RuntimeError(
                "No OCR provider selected."
            )

        return self.active_provider.recognize(
            image_path
        )

    def recognize_batch(
        self,
        image_paths,
    ):

        results = []

        for image in image_paths:

            results.append(
                self.recognize(image)
            )

        return results