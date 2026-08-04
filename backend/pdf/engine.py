import fitz
from pathlib import Path

from backend.pdf.metadata import PDFMetadata
from backend.pdf.search import PDFSearch
from backend.pdf.session import PDFSession
from backend.pdf.renderer import PDFRenderer
from backend.pdf.thumbnail import ThumbnailGenerator


class PDFEngine:
    """
    Main PDF engine for AI Content Studio.

    Responsibilities
    ----------------
    • Open PDF files
    • Read metadata
    • Extract text
    • Render pages
    • Generate thumbnails
    • Search text
    • Save/restore viewing session
    """

    def __init__(self):

        self.renderer = PDFRenderer()

        self.thumbnail_generator = ThumbnailGenerator()

        self.search_engine = PDFSearch()

    # --------------------------------------------------
    # PDF
    # --------------------------------------------------

    def open(self, filename):

        return fitz.open(filename)

    # --------------------------------------------------
    # Metadata
    # --------------------------------------------------

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

    # --------------------------------------------------
    # Page Access
    # --------------------------------------------------

    def page(self, pdf, page_number):

        return pdf.load_page(page_number)

    def page_count(self, pdf):

        return len(pdf)

    # --------------------------------------------------
    # Text Extraction
    # --------------------------------------------------

    def extract_page_text(
        self,
        pdf,
        page_number,
    ):

        page = pdf.load_page(page_number)

        return page.get_text()

    def extract_all_text(
        self,
        pdf,
    ):

        pages = []

        for i in range(len(pdf)):

            pages.append(

                self.extract_page_text(
                    pdf,
                    i,
                )

            )

        return pages

    # --------------------------------------------------
    # Rendering
    # --------------------------------------------------

    def page_image(
        self,
        pdf,
        page_number,
        dpi=200,
    ):

        return self.renderer.render_page(

            pdf,

            page_number,

            dpi,

        )

    # --------------------------------------------------
    # Thumbnail
    # --------------------------------------------------

    def page_thumbnail(
        self,
        pdf,
        page_number,
        filename,
    ):

        self.thumbnail_generator.create(

            pdf,

            page_number,

            filename,

        )

    # --------------------------------------------------
    # Search
    # --------------------------------------------------

    def search_text(
        self,
        pdf,
        keyword,
    ):

        pages = self.extract_all_text(pdf)

        return self.search_engine.search(

            pages,

            keyword,

        )

    # --------------------------------------------------
    # Session
    # --------------------------------------------------

    def save_session(
        self,
        project_folder,
        page,
        zoom,
    ):

        session = PDFSession(project_folder)

        session.save(

            page,

            zoom,

        )

    def restore_session(
        self,
        project_folder,
    ):

        session = PDFSession(project_folder)

        return session.load()

    # --------------------------------------------------
    # Close
    # --------------------------------------------------

    def close(
        self,
        pdf,
    ):

        if pdf:

            pdf.close()