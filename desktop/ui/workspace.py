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
