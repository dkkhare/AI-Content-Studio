import fitz

from backend.pdf.metadata import PDFMetadata


class PDFEngine:

    def open(self, filename):

        return fitz.open(filename)

    def metadata(self, pdf):

        meta = pdf.metadata

        return PDFMetadata(
            title=meta.get("title", ""),
            author=meta.get("author", ""),
            subject=meta.get("subject", ""),
            creator=meta.get("creator", ""),
            producer=meta.get("producer", ""),
            page_count=len(pdf),
        )