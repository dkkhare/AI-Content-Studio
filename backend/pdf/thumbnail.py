import fitz


class ThumbnailGenerator:

    def create(
        self,
        pdf,
        page_number,
        filename,
    ):

        page = pdf.load_page(page_number)

        pix = page.get_pixmap(
            matrix=fitz.Matrix(0.2, 0.2)
        )

        pix.save(filename)