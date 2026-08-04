from pathlib import Path

from PySide6.QtWidgets import QFileDialog
from PySide6.QtWidgets import QMessageBox

from backend.pdf.engine import PDFEngine
from backend.pdf.session import PDFSession


class PDFController:
    """
    Controller responsible for PDF operations.

    Responsibilities
    ----------------
    • Open PDF
    • Close PDF
    • Search text
    • Save session
    • Restore session
    • Jump to page
    • Export text
    """

    def __init__(self, window):

        self.window = window

        self.engine = PDFEngine()

        self.pdf = None

        self.filename = None

        self.metadata = None

        self.project_folder = None

    # --------------------------------------------------
    # Open PDF
    # --------------------------------------------------

    def open_pdf(self):

        filename, _ = QFileDialog.getOpenFileName(

            self.window,

            "Open Poetry Book",

            str(Path.home()),

            "PDF Files (*.pdf)",

        )

        if not filename:

            return None

        self.filename = filename

        self.pdf = self.engine.open(filename)

        self.metadata = self.engine.metadata(self.pdf)

        self.project_folder = str(
            Path(filename).parent
        )

        self.window.statusBar().showMessage(

            f"Loaded {self.metadata.page_count} pages"

        )

        return self.pdf

    # --------------------------------------------------
    # Close PDF
    # --------------------------------------------------

    def close_pdf(self):

        if self.pdf:

            self.engine.close(self.pdf)

            self.pdf = None

    # --------------------------------------------------
    # Metadata
    # --------------------------------------------------

    def get_metadata(self):

        return self.metadata

    # --------------------------------------------------
    # Search
    # --------------------------------------------------

    def search(self, keyword):

        if self.pdf is None:

            return []

        return self.engine.search_text(

            self.pdf,

            keyword,

        )

    # --------------------------------------------------
    # Jump to Page
    # --------------------------------------------------

    def jump_to_page(

        self,

        page_number,

    ):

        if self.pdf is None:

            return None

        if page_number < 1:

            page_number = 1

        if page_number > len(self.pdf):

            page_number = len(self.pdf)

        return self.engine.page(

            self.pdf,

            page_number - 1,

        )

    # --------------------------------------------------
    # Export Text
    # --------------------------------------------------

    def export_text(self):

        if self.pdf is None:

            return []

        return self.engine.extract_all_text(

            self.pdf

        )

    # --------------------------------------------------
    # Session
    # --------------------------------------------------

    def save_session(

        self,

        current_page,

        zoom,

    ):

        if self.project_folder is None:

            return

        self.engine.save_session(

            self.project_folder,

            current_page,

            zoom,

        )

    def restore_session(self):

        if self.project_folder is None:

            return None

        return self.engine.restore_session(

            self.project_folder

        )

    # --------------------------------------------------
    # Information
    # --------------------------------------------------

    def page_count(self):

        if self.pdf is None:

            return 0

        return self.engine.page_count(

            self.pdf

        )

    # --------------------------------------------------
    # About PDF
    # --------------------------------------------------

    def show_information(self):

        if self.metadata is None:

            return

        QMessageBox.information(

            self.window,

            "PDF Information",

            (
                f"Title : {self.metadata.title}\n"
                f"Author : {self.metadata.author}\n"
                f"Pages : {self.metadata.page_count}"
            ),

        )