from dataclasses import dataclass, field

from backend.pdf.metadata import PDFMetadata


@dataclass
class PDFDocumentModel:

    filename: str = ""

    metadata: PDFMetadata | None = None

    current_page: int = 1

    zoom: float = 1.0

    page_count: int = 0

    thumbnails: list[str] = field(default_factory=list)