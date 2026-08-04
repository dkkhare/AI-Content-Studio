import fitz


class PDFRenderer:

    def render_page(
        self,
        pdf,
        page_number,
        dpi=200,
    ):

        page = pdf.load_page(page_number)

        matrix = fitz.Matrix(
            dpi / 72,
            dpi / 72,
        )

        pix = page.get_pixmap(
            matrix=matrix
        )

        return pix