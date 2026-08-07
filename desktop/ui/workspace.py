from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDialog, QLabel, QMessageBox, QTabWidget, QVBoxLayout, QWidget

from desktop.ui.dialogs.processing_setup_dialog import ProcessingSetupDialog
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
        self.workflow_panel.startRequested.connect(self.start_processing)
        self.tabs.addTab(self.workflow_panel, "Processing")

    def set_pipeline_controller(self, controller) -> None:
        if self.pipeline_controller is controller:
            return
        self.pipeline_controller = controller
        self.workflow_panel.bind_controller(controller)
        controller.started.connect(lambda: self.set_busy(True))
        controller.completed.connect(lambda state: self.set_busy(False))
        controller.cancelled.connect(lambda: self.set_busy(False))
        controller.failed.connect(lambda message: self.set_busy(False))
        controller.queueChanged.connect(self._on_queue_changed)

    def _on_queue_changed(self, records) -> None:
        self._busy = any(
            str(item.get("status", "")) in {"running", "paused"}
            for item in (records or [])
        )

    def start_processing(self) -> bool:
        if self.current_project is None or self.pipeline_controller is None:
            return False

        dialog = ProcessingSetupDialog(self.current_project, self)
        if dialog.exec() != QDialog.Accepted:
            return False

        data = dialog.data()
        if self.current_project.get_setting("pipeline_ocr_enabled", True) and not data["ocr_images"]:
            QMessageBox.warning(
                self,
                "Queue Processing",
                "OCR is enabled, but no source images were selected.",
            )
            return False

        try:
            job = self.pipeline_controller.submit_project(
                self.current_project,
                data=data,
                priority=dialog.queue_priority(),
                resume=True,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Unable to Queue Processing", str(exc))
            return False

        if job is not None:
            self.open_processing_tab()
            return True
        return False

    def open_project(self, project) -> None:
        self.current_project = project
        self._busy = False
        if self.workflow_panel:
            self.workflow_panel.set_project_available(True)
        self.refresh()
        self.open_pdf_tab()
        self.projectOpened.emit(str(project))

    def close_project(self) -> None:
        self.current_project = None
        self._busy = False
        if self.workflow_panel:
            self.workflow_panel.set_project_available(False)
            if not (
                self.pipeline_controller
                and (self.pipeline_controller.running or self.pipeline_controller.queue_running)
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

    def set_busy(self, busy: bool) -> None:
        self._busy = bool(busy)

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

    def clear(self) -> None:
        self._busy = False
        self.current_project = None
        if self.workflow_panel:
            self.workflow_panel.set_project_available(False)
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
