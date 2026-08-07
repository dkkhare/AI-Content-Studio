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

from backend.images import VisualAssetReviewStore


class VisualReviewPanel(QWidget):
    """Human review surface for generated local visual assets."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = None
        self.review_store = None
        self.summary = QLabel("Open a project to review generated visuals.", self)
        self.summary.setWordWrap(True)
        self.table = QTableWidget(0, 5, self)
        self.table.setHorizontalHeaderLabels(["Type", "Owner", "Status", "Path", "ID"])
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
        layout.addWidget(QLabel("Prompt / Asset Details", self))
        layout.addWidget(self.details, 1)
        buttons = QHBoxLayout()
        for button in (self.approve_button, self.skip_button, self.regenerate_button, self.refresh_button):
            buttons.addWidget(button)
        buttons.addStretch()
        layout.addLayout(buttons)

    def set_project(self, project) -> None:
        self.project = project
        self.review_store = VisualAssetReviewStore(project.root)
        self.refresh()

    def clear(self) -> None:
        self.project = None
        self.review_store = None
        self.table.setRowCount(0)
        self.details.clear()
        self.summary.setText("Open a project to review generated visuals.")

    def refresh(self) -> None:
        self.table.setRowCount(0)
        self.details.clear()
        if self.review_store is None:
            return
        items = self.review_store.items()
        pending = len(self.review_store.pending())
        self.summary.setText(f"Visual assets: {len(items)} total • {pending} pending review")
        for item in items:
            asset_type = str(item.get("asset_type", ""))
            if asset_type not in {"character_reference", "location_reference", "scene_image"}:
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                asset_type.replace("_", " ").title(),
                str(item.get("owner_id", "")),
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
        item = self.table.item(row, 4)
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
        references = "\n".join(str(value) for value in item.get("reference_paths", []) if str(value))
        text = (
            f"Path: {item.get('path', '')}\n\n"
            f"Prompt:\n{item.get('prompt', '')}\n"
        )
        if references:
            text += f"\nApproved references used:\n{references}\n"
        self.details.setPlainText(text)

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
