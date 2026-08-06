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

        self.session = PDFSession()

        self.pdf = None

        self.filename = None

        self.metadata = None

        self.project_folder = None

        self.current_page = 1

        self.zoom = 1.0

        self.is_modified = False

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

        try:

            self.filename = filename

            self.pdf = self.engine.open(filename)

            self.metadata = self.engine.metadata(self.pdf)

            self.project_folder = str(
                Path(filename).parent
            )

            self.current_page = 1

            self.zoom = 1.0

            self.is_modified = False

            self.window.statusBar().showMessage(

                f"Loaded {self.metadata.page_count} pages"

            )

            return self.pdf

        except Exception as exc:

            self.pdf = None

            self.metadata = None

            self.filename = None

            self.project_folder = None

            QMessageBox.critical(

                self.window,

                "Open PDF",

                str(exc),

            )

            return None

    # --------------------------------------------------
    # Close PDF
    # --------------------------------------------------

    def close_pdf(self):

        if self.pdf:

            try:

                self.engine.close(self.pdf)

            except Exception:

                pass

        self.pdf = None

        self.metadata = None

        self.filename = None

        self.project_folder = None

        self.current_page = 1

        self.zoom = 1.0

        self.is_modified = False

    # --------------------------------------------------
    # Metadata
    # --------------------------------------------------

    def get_metadata(self):

        return self.metadata

    # --------------------------------------------------
    # State Helpers
    # --------------------------------------------------

    def has_pdf(self):

        return self.pdf is not None

    def current_pdf(self):

        return self.pdf

    def current_filename(self):

        return self.filename

    def current_project_folder(self):

        return self.project_folder
    # --------------------------------------------------
    # Search
    # --------------------------------------------------

    def search(
        self,
        keyword,
    ):

        if self.pdf is None:

            return []

        if not keyword:

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

        total_pages = self.page_count()

        if total_pages == 0:

            return None

        page_number = max(
            1,
            min(page_number, total_pages),
        )

        self.current_page = page_number

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

        self.current_page = current_page

        self.zoom = zoom

        self.engine.save_session(

            self.project_folder,

            current_page,

            zoom,

        )

    def restore_session(self):

        if self.project_folder is None:

            return None

        session = self.engine.restore_session(

            self.project_folder

        )

        if session:

            try:

                self.current_page = session.current_page

                self.zoom = session.zoom

            except AttributeError:

                pass

        return session

    # --------------------------------------------------
    # Information
    # --------------------------------------------------

    def page_count(self):

        if self.pdf is None:

            return 0

        return self.engine.page_count(

            self.pdf

        )

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

    # --------------------------------------------------
    # Utility
    # --------------------------------------------------

    def is_open(self):

        return self.pdf is not None

    def mark_modified(self):

        self.is_modified = True

    def clear_modified(self):

        self.is_modified = False

    def current_state(self):

        return {

            "filename": self.filename,

            "project_folder": self.project_folder,

            "current_page": self.current_page,

            "zoom": self.zoom,

            "modified": self.is_modified,

        }