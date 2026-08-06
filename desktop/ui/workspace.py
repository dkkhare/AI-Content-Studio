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
    Main production workspace.

    Handles the editor area after a project
    has been opened.

    Responsibilities:
    - Host production tools
    - Manage tabs
    - Refresh project views

    Business operations are handled by
    ProjectController/backend services.
    """

    projectOpened = Signal(str)

    projectClosed = Signal()


    def __init__(
        self,
        parent=None,
    ):

        super().__init__(
            parent
        )


        self.current_project = None


        self.tabs = None


        self.pdf_page = None

        self.ocr_page = None

        self.translation_page = None

        self.video_page = None

        self.export_page = None

        self.narration_panel = None


        self._build_ui()


    # --------------------------------------------------
    # UI Construction
    # --------------------------------------------------

    def _build_ui(
        self,
    ):

        layout = QVBoxLayout(
            self
        )


        self.tabs = QTabWidget()


        layout.addWidget(
            self.tabs
        )


        self._create_tabs()


    # --------------------------------------------------
    # Tabs
    # --------------------------------------------------

    def _create_tabs(
        self,
    ):

        self._create_pdf_tab()

        self._create_ocr_tab()

        self._create_narration_tab()

        self._create_translation_tab()

        self._create_video_tab()

        self._create_export_tab()
    # --------------------------------------------------
    # Tab Creation
    # --------------------------------------------------

    def _create_pdf_tab(
        self,
    ):

        self.pdf_page = QLabel(
            "PDF Viewer\n\n"
            "PDF processing workspace."
        )

        self.pdf_page.setWordWrap(
            True
        )

        self.tabs.addTab(
            self.pdf_page,
            "PDF",
        )


    def _create_ocr_tab(
        self,
    ):

        self.ocr_page = QLabel(
            "OCR Workspace\n\n"
            "OCR processing tools."
        )

        self.ocr_page.setWordWrap(
            True
        )

        self.tabs.addTab(
            self.ocr_page,
            "OCR",
        )


    def _create_narration_tab(
        self,
    ):

        self.narration_panel = NarrationPanel()

        self.tabs.addTab(
            self.narration_panel,
            "Narration",
        )


    def _create_translation_tab(
        self,
    ):

        self.translation_page = QLabel(
            "Translation\n\n"
            "Translation tools."
        )

        self.translation_page.setWordWrap(
            True
        )

        self.tabs.addTab(
            self.translation_page,
            "Translation",
        )


    def _create_video_tab(
        self,
    ):

        self.video_page = QLabel(
            "Video Generation\n\n"
            "Video generation tools."
        )

        self.video_page.setWordWrap(
            True
        )

        self.tabs.addTab(
            self.video_page,
            "Video",
        )


    def _create_export_tab(
        self,
    ):

        self.export_page = QLabel(
            "Export\n\n"
            "Export and publishing tools."
        )

        self.export_page.setWordWrap(
            True
        )

        self.tabs.addTab(
            self.export_page,
            "Export",
        )
    # --------------------------------------------------
    # Project Handling
    # --------------------------------------------------

    def open_project(
        self,
        project,
    ):

        """
        Load project into workspace.

        Project data handling remains outside
        this widget.
        """

        self.current_project = project


        self.refresh()


        self.projectOpened.emit(
            str(project)
        )


    def close_project(
        self,
    ):

        self.current_project = None


        self.clear()


        self.projectClosed.emit()


    # --------------------------------------------------
    # Refresh
    # --------------------------------------------------

    def refresh(
        self,
    ):

        """
        Refresh all child widgets.
        """

        if self.narration_panel:

            if hasattr(
                self.narration_panel,
                "refresh",
            ):

                self.narration_panel.refresh()



    # --------------------------------------------------
    # Tab Helpers
    # --------------------------------------------------

    def narration(
        self,
    ):

        return self.narration_panel


    def current_tab(
        self,
    ) -> int:

        return self.tabs.currentIndex()


    def set_current_tab(
        self,
        index: int,
    ):

        if 0 <= index < self.tabs.count():

            self.tabs.setCurrentIndex(
                index
            )


    def open_pdf_tab(
        self,
    ):

        self.set_current_tab(
            0
        )


    def open_ocr_tab(
        self,
    ):

        self.set_current_tab(
            1
        )


    def open_narration_tab(
        self,
    ):

        self.set_current_tab(
            2
        )


    def open_translation_tab(
        self,
    ):

        self.set_current_tab(
            3
        )


    def open_video_tab(
        self,
    ):

        self.set_current_tab(
            4
        )


    def open_export_tab(
        self,
    ):

        self.set_current_tab(
            5
        )


    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def clear(
        self,
    ):

        """
        Clear project-specific UI state.
        """

        if self.narration_panel:

            if hasattr(
                self.narration_panel,
                "clear",
            ):

                self.narration_panel.clear()



    def dispose(
        self,
    ):

        self.clear()

        self.current_project = None
