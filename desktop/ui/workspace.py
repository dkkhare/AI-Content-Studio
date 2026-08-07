from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QTabWidget, QVBoxLayout, QWidget

from desktop.ui.widgets.narration_panel import NarrationPanel
from desktop.ui.workflow_panel import WorkflowPanel


class Workspace(QWidget):
    """Main production workspace; business logic remains in controllers."""

    projectOpened = Signal(str)
    projectClosed = Signal()
    tabChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_project = None
        self.pipeline_controller = None
        self._busy = False

        self.tabs = QTabWidget(self)
        self.pdf_page = None
        self.ocr_page = None
        self.narration_panel = None
        self.translation_page = None
        self.video_page = None
        self.export_page = None
        self.workflow_panel = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        self.tabs.setDocumentMode(True)
        self.tabs.setMovable(False)
        self.tabs.currentChanged.connect(self.tabChanged.emit)
        layout.addWidget(self.tabs)
        self._create_tabs()

    @staticmethod
    def _placeholder(title: str, text: str) -> QLabel:
        label = QLabel(f"{title}\n\n{text}")
        label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        label.setWordWrap(True)
        return label

    def _create_tabs(self) -> None:
        self.pdf_page = self._placeholder("PDF Viewer", "PDF processing workspace.")
        self.tabs.addTab(self.pdf_page, "PDF")

        self.ocr_page = self._placeholder("OCR Workspace", "OCR processing tools.")
        self.tabs.addTab(self.ocr_page, "OCR")

        self.narration_panel = NarrationPanel()
        self.tabs.addTab(self.narration_panel, "Narration")

        self.translation_page = self._placeholder("Translation", "Translation tools.")
        self.tabs.addTab(self.translation_page, "Translation")

        self.video_page = self._placeholder("Video Generation", "Video generation tools.")
        self.tabs.addTab(self.video_page, "Video")

        self.export_page = self._placeholder("Export", "Export and publishing tools.")
        self.tabs.addTab(self.export_page, "Export")

        self.workflow_panel = WorkflowPanel(self)
        self.tabs.addTab(self.workflow_panel, "Processing")

    # --------------------------------------------------
    # Controller integration
    # --------------------------------------------------

    def set_pipeline_controller(self, controller) -> None:
        if self.pipeline_controller is controller:
            return
        self.pipeline_controller = controller
        self.workflow_panel.bind_controller(controller)
        controller.started.connect(lambda: self.set_busy(True))
        controller.completed.connect(lambda state: self.set_busy(False))
        controller.cancelled.connect(lambda: self.set_busy(False))
        controller.failed.connect(lambda message: self.set_busy(False))

    # --------------------------------------------------
    # Project handling
    # --------------------------------------------------

    def open_project(self, project) -> None:
        self.current_project = project
        self._busy = False
        self.refresh()
        self.open_pdf_tab()
        self.projectOpened.emit(str(project))

    def close_project(self) -> None:
        self.current_project = None
        self._busy = False
        if self.workflow_panel and not (
            self.pipeline_controller and self.pipeline_controller.running
        ):
            self.workflow_panel.reset()
        self.clear()
        self.projectClosed.emit()

    def refresh(self) -> None:
        if self.narration_panel and hasattr(self.narration_panel, "refresh"):
            try:
                self.narration_panel.refresh()
            except Exception:
                pass

    # --------------------------------------------------
    # State / tabs
    # --------------------------------------------------

    def set_busy(self, busy: bool) -> None:
        self._busy = bool(busy)
        # Keep the Processing tab usable while work is running so users can
        # pause, resume, or cancel. Other tabs remain readable as well.

    def is_busy(self) -> bool:
        return self._busy

    def narration(self):
        return self.narration_panel

    def processing(self):
        return self.workflow_panel

    def current_tab(self) -> int:
        return self.tabs.currentIndex()

    def set_current_tab(self, index: int) -> None:
        if 0 <= index < self.tabs.count():
            self.tabs.setCurrentIndex(index)

    def current_tab_name(self) -> str:
        return self.tabs.tabText(self.tabs.currentIndex())

    def open_pdf_tab(self) -> None:
        self.set_current_tab(0)

    def open_ocr_tab(self) -> None:
        self.set_current_tab(1)

    def open_narration_tab(self) -> None:
        self.set_current_tab(2)

    def open_translation_tab(self) -> None:
        self.set_current_tab(3)

    def open_video_tab(self) -> None:
        self.set_current_tab(4)

    def open_export_tab(self) -> None:
        self.set_current_tab(5)

    def open_processing_tab(self) -> None:
        self.set_current_tab(6)

    # --------------------------------------------------
    # Cleanup / information
    # --------------------------------------------------

    def clear(self) -> None:
        self._busy = False
        self.current_project = None
        if self.narration_panel and hasattr(self.narration_panel, "clear"):
            try:
                self.narration_panel.clear()
            except Exception:
                pass
        self.set_current_tab(0)

    def has_project(self) -> bool:
        return self.current_project is not None

    def project(self):
        return self.current_project

    def tab_count(self) -> int:
        return self.tabs.count()

    def dispose(self) -> None:
        if self.pipeline_controller and self.pipeline_controller.running:
            self.pipeline_controller.cancel()
        self.clear()
        self.pipeline_controller = None
