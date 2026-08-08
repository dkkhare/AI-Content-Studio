from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QLabel,
)


class Workspace(QWidget):
    """
    Main production workspace.

    Hosts all production tabs while business
    logic remains inside controllers.
    """

    projectOpened = Signal(str)

    projectClosed = Signal()

    tabChanged = Signal(int)

    def __init__(
        self,
        parent=None,
    ):

        super().__init__(parent)

        self.current_project = None

        self.tabs = None

        self.pdf_page = None

        self.ocr_page = None

        self.subtitle_panel = None

        self.translation_page = None

        self.video_page = None

        self.export_page = None

        self.narration_panel = None

        self._busy = False

        self._build_ui()

    # --------------------------------------------------
    # UI Construction
    # --------------------------------------------------

    def _build_ui(
        self,
    ):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            8,
            8,
            8,
            8,
        )

        self.tabs = QTabWidget()

        self.tabs.setDocumentMode(True)

        self.tabs.setMovable(False)

        self.tabs.currentChanged.connect(
            self.tabChanged.emit
        )

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

        self._create_subtitle_tab()

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

        self.pdf_page.setAlignment(
            Qt.AlignTop | Qt.AlignLeft
        )

        self.pdf_page.setWordWrap(True)

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

        self.ocr_page.setAlignment(
            Qt.AlignTop | Qt.AlignLeft
        )

        self.ocr_page.setWordWrap(True)

        self.tabs.addTab(
            self.ocr_page,
            "OCR",
        )

    def _create_narration_tab(
        self,
    ):

        try:
            from desktop.ui.widgets.narration_panel import NarrationPanel

            self.narration_panel = NarrationPanel()
        except (ImportError, ModuleNotFoundError) as exc:
            self.narration_panel = QLabel(
                "Narration unavailable\n\n"
                f"Optional TTS components could not be loaded: {exc}"
            )
            self.narration_panel.setWordWrap(True)
            self.narration_panel.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.tabs.addTab(
            self.narration_panel,
            "Narration",
        )

    def _create_subtitle_tab(
        self,
    ):

        from desktop.ui.widgets.subtitle_panel import SubtitlePanel

        self.subtitle_panel = SubtitlePanel()

        self.tabs.addTab(
            self.subtitle_panel,
            "Subtitles",
        )

    def _create_translation_tab(
        self,
    ):

        self.translation_page = QLabel(
            "Translation\n\n"
            "Translation tools."
        )

        self.translation_page.setAlignment(
            Qt.AlignTop | Qt.AlignLeft
        )

        self.translation_page.setWordWrap(True)

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

        self.video_page.setAlignment(
            Qt.AlignTop | Qt.AlignLeft
        )

        self.video_page.setWordWrap(True)

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

        self.export_page.setAlignment(
            Qt.AlignTop | Qt.AlignLeft
        )

        self.export_page.setWordWrap(True)

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
        """

        self.current_project = project

        if self.subtitle_panel:
            self.subtitle_panel.set_project(project)

        self._busy = False

        self.refresh()

        self.open_pdf_tab()

        self.projectOpened.emit(
            str(project)
        )

    def close_project(
        self,
    ):

        self.current_project = None

        self._busy = False

        self.clear()

        self.projectClosed.emit()

    # --------------------------------------------------
    # Refresh
    # --------------------------------------------------

    def refresh(
        self,
    ):

        if self.narration_panel:

            if hasattr(
                self.narration_panel,
                "refresh",
            ):

                try:

                    self.narration_panel.refresh()

                except Exception:

                    pass

    # --------------------------------------------------
    # Workspace State
    # --------------------------------------------------

    def set_busy(
        self,
        busy: bool,
    ):

        self._busy = busy

        self.tabs.setEnabled(
            not busy
        )

    def is_busy(
        self,
    ) -> bool:

        return self._busy

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

    def current_tab_name(
        self,
    ) -> str:

        return self.tabs.tabText(
            self.tabs.currentIndex()
        )

    def open_pdf_tab(
        self,
    ):

        self.set_current_tab(0)

    def open_ocr_tab(
        self,
    ):

        self.set_current_tab(1)

    def open_narration_tab(
        self,
    ):

        self.set_current_tab(2)

    def open_translation_tab(
        self,
    ):

        self.set_current_tab(4)

    def open_subtitle_tab(
        self,
    ):

        self.set_current_tab(3)

    def open_video_tab(
        self,
    ):

        self.set_current_tab(5)

    def open_export_tab(
        self,
    ):

        self.set_current_tab(6)
    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def clear(
        self,
    ):
        """
        Clear project-specific UI state.
        """

        self._busy = False

        self.current_project = None

        if self.narration_panel:

            if hasattr(
                self.narration_panel,
                "clear",
            ):

                try:

                    self.narration_panel.clear()

                except Exception:

                    pass

        if self.subtitle_panel:
            self.subtitle_panel.clear()

        self.set_current_tab(0)

    # --------------------------------------------------
    # Information
    # --------------------------------------------------

    def has_project(
        self,
    ) -> bool:

        return self.current_project is not None

    def project(
        self,
    ):

        return self.current_project

    def tab_count(
        self,
    ) -> int:

        return self.tabs.count()

    # --------------------------------------------------
    # Disposal
    # --------------------------------------------------

    def dispose(
        self,
    ):

        if self.narration_panel and hasattr(self.narration_panel, "cleanup"):
            try:
                self.narration_panel.cleanup()
            except Exception:
                pass

        self.clear()

        self.tabs = None

        self.pdf_page = None

        self.ocr_page = None

        if self.subtitle_panel and hasattr(self.subtitle_panel, "dispose"):
            self.subtitle_panel.dispose()

        self.subtitle_panel = None

        self.translation_page = None

        self.video_page = None

        self.export_page = None

        self.narration_panel = None