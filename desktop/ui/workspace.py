from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QLabel,
)

from desktop.ui.widgets.narration_panel import NarrationPanel


class Workspace(QWidget):
    """
    Main project workspace.

    This widget hosts all major production tools.
    """

    projectOpened = Signal(str)
    projectClosed = Signal()

    def __init__(self, parent=None):

        super().__init__(parent)

        self._build_ui()
    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def _build_ui(self):

        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()

        layout.addWidget(self.tabs)

        self._create_tabs()
    # --------------------------------------------------
    # Tabs
    # --------------------------------------------------

    def _create_tabs(self):

        #
        # PDF
        #

        self.pdf_page = QLabel(

            "PDF Viewer\n\n"

            "Will be implemented in the next milestone."

        )

        self.pdf_page.setWordWrap(True)

        self.tabs.addTab(

            self.pdf_page,

            "PDF",

        )

        #
        # OCR
        #

        self.ocr_page = QLabel(

            "OCR Workspace\n\n"

            "Coming soon."

        )

        self.ocr_page.setWordWrap(True)

        self.tabs.addTab(

            self.ocr_page,

            "OCR",

        )

        #
        # Narration
        #

        self.narration_panel = NarrationPanel()

        self.tabs.addTab(

            self.narration_panel,

            "Narration",

        )

        #
        # Translation
        #

        self.translation_page = QLabel(

            "Translation\n\n"

            "Coming soon."

        )

        self.translation_page.setWordWrap(True)

        self.tabs.addTab(

            self.translation_page,

            "Translation",

        )

        #
        # Video
        #

        self.video_page = QLabel(

            "Video Generation\n\n"

            "Coming soon."

        )

        self.video_page.setWordWrap(True)

        self.tabs.addTab(

            self.video_page,

            "Video",

        )

        #
        # Export
        #

        self.export_page = QLabel(

            "Export\n\n"

            "Coming soon."

        )

        self.export_page.setWordWrap(True)

        self.tabs.addTab(

            self.export_page,

            "Export",

        )
    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def narration(self):

        return self.narration_panel

    def current_tab(self):

        return self.tabs.currentIndex()

    def set_current_tab(

        self,

        index,

    ):

        self.tabs.setCurrentIndex(index)

    def open_pdf_tab(self):

        self.tabs.setCurrentIndex(0)

    def open_ocr_tab(self):

        self.tabs.setCurrentIndex(1)

    def open_narration_tab(self):

        self.tabs.setCurrentIndex(2)

    def open_translation_tab(self):

        self.tabs.setCurrentIndex(3)

    def open_video_tab(self):

        self.tabs.setCurrentIndex(4)

    def open_export_tab(self):

        self.tabs.setCurrentIndex(5)
    # --------------------------------------------------
    # Project
    # --------------------------------------------------

    def open_project(

        self,

        project_path,

    ):

        self.projectOpened.emit(

            project_path

        )

    def close_project(self):

        self.projectClosed.emit()
