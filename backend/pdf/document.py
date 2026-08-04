from dataclasses import dataclass, field

from typing import List


@dataclass
class PDFPage:

    number: int

    text: str = ""

    image = None


@dataclass
class PDFDocument:

    filename: str

    page_count: int

    pages: List[PDFPage] = field(default_factory=list)