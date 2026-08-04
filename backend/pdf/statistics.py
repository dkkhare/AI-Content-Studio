from dataclasses import dataclass


@dataclass
class PDFStatistics:
    pages_processed: int = 0
    text_pages: int = 0
    scanned_pages: int = 0
    images_created: int = 0