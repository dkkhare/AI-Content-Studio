from pathlib import Path

import fitz

from backend.pdf.document import PDFDocument


class PDFImporter:

    def open(self, filename: str):

        pdf = fitz.open(filename)

        return PDFDocument(
            filename=filename,
            page_count=len(pdf),
        )