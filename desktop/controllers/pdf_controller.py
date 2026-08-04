from pathlib import Path

from PySide6.QtWidgets import QFileDialog

from backend.pdf.engine import PDFEngine


class PDFController:

    def __init__(self, window):

        self.window = window

        self.engine = PDFEngine()

    def open_pdf(self):

        filename, _ = QFileDialog.getOpenFileName(

            self.window,

            "Open Poetry Book",

            str(Path.home()),

            "PDF Files (*.pdf)",

        )

        if not filename:

            return

        pdf = self.engine.open(filename)

        metadata = self.engine.metadata(pdf)

        self.window.statusBar().showMessage(

            f"Loaded {metadata.page_count} pages"

        )

        return pdf