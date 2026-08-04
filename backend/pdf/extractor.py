import fitz

from backend.pdf.document import PDFPage


class TextExtractor:

    def extract(self, filename):

        pdf = fitz.open(filename)

        pages = []

        for number, page in enumerate(pdf):

            text = page.get_text()

            pages.append(
                PDFPage(
                    number + 1,
                    text,
                )
            )

        return pages
