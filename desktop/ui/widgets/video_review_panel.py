from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from backend.video import VideoAssetReviewStore


class VideoReviewPanel(QWidget):
    """Human review surface for locally generated scene clips."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = None
        self.review_store = None
        self.summary = QLabel("Open a project to review generated scene clips.", self)
        self.summary.setWordWrap(True)
        self.table = QTableWidget(0, 6, self)
        self.table.setHorizontalHeaderLabels(["Episode", "Scene", "Duration", "Status", "Path", "ID"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self._load_selected)
        self.details = QTextEdit(self)
        self.details.setReadOnly(True)
        self.approve_button = QPushButton("Approve", self)
        self.skip_button = QPushButton("Skip", self)
        self.regenerate_button = QPushButton("Regenerate", self)
        self.refresh_button = QPushButton("Refresh", self)
        self.approve_button.clicked.connect(self.approve_selected)
        self.skip_button.clicked.connect(self.skip_selected)
        self.regenerate_button.clicked.connect(self.regenerate_selected)
        self.refresh_button.clicked.connect(self.refresh)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(self.summary)
        layout.addWidget(self.table, 2)
        layout.addWidget(QLabel("Video Prompt / Source", self))
        layout.addWidget(self.details, 1)
        buttons = QHBoxLayout()
        for button in (self.approve_button, self.skip_button, self.regenerate_button, self.refresh_button):
            buttons.addWidget(button)
        buttons.addStretch()
        layout.addLayout(buttons)

    def set_project(self, project) -> None:
        self.project = project
        self.review_store = VideoAssetReviewStore(project.root)
        self.refresh()

    def clear(self) -> None:
        self.project = None
        self.review_store = None
        self.table.setRowCount(0)
        self.details.clear()
        self.summary.setText("Open a project to review generated scene clips.")

    def refresh(self) -> None:
        self.table.setRowCount(0)
        self.details.clear()
        if self.review_store is None:
            return
        counts = self.review_store.counts()
        self.summary.setText(
            f"Scene clips: {counts['total']} total • {counts['approved']} approved • "
            f"{counts['skipped']} skipped • {counts['pending']} pending"
        )
        for item in self.review_store.items("scene_video"):
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                str(item.get("episode_id", "")),
                str(item.get("owner_id", "")),
                f"{float(item.get('duration_seconds', 0) or 0):.1f}s",
                str(item.get("status", "pending_review")),
                str(item.get("path", "")),
                str(item.get("id", "")),
            ]
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                cell.setFlags(cell.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, column, cell)
        self.table.resizeColumnsToContents()

    def _selected_id(self) -> str:
        row = self.table.currentRow()
        if row < 0:
            return ""
        item = self.table.item(row, 5)
        return item.text().strip() if item else ""

    def _load_selected(self) -> None:
        asset_id = self._selected_id()
        if not asset_id or self.review_store is None:
            self.details.clear()
            return
        try:
            item = self.review_store.get(asset_id)
        except Exception:
            self.details.clear()
            return
        self.details.setPlainText(
            f"Source image: {item.get('source_image_path', '')}\n"
            f"Output: {item.get('path', '')}\n"
            f"Provider: {item.get('provider', '')}\n"
            f"Duration: {item.get('duration_seconds', '')}\n\n"
            f"Video prompt:\n{item.get('prompt', '')}"
        )

    def approve_selected(self) -> None:
        asset_id = self._selected_id()
        if asset_id and self.review_store is not None:
            self.review_store.approve(asset_id)
            self.refresh()

    def skip_selected(self) -> None:
        asset_id = self._selected_id()
        if asset_id and self.review_store is not None:
            self.review_store.skip(asset_id)
            self.refresh()

    def regenerate_selected(self) -> None:
        asset_id = self._selected_id()
        if asset_id and self.review_store is not None:
            self.review_store.request_regeneration(asset_id)
            self.refresh()
