from dataclasses import dataclass


@dataclass
class PDFImportReport:

    pages: int

    text_pages: int

    scanned_pages: int

    ocr_pages: int

    elapsed_seconds: float