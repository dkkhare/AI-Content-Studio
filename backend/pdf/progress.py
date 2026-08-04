from dataclasses import dataclass


@dataclass
class PDFProgress:
    current_page: int = 0
    total_pages: int = 0
    percent: int = 0
    status: str = ""