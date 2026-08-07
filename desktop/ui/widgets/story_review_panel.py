from __future__ import annotations

import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from backend.knowledge import KnowledgeReviewStore


class _CollectionReviewPage(QWidget):
    def __init__(self, collection: str, parent=None):
        super().__init__(parent)
        self.collection = collection
        self.review_store = None
        self.table = QTableWidget(0, 4, self)
        self.table.setHorizontalHeaderLabels(["Name / Relation", "Status", "Approved", "ID"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self._load_selected)
        self.editor = QTextEdit(self)
        self.editor.setPlaceholderText("Selected knowledge item JSON. Edit fields, then click Save Edit.")
        self.approve_button = QPushButton("Approve", self)
        self.save_button = QPushButton("Save Edit", self)
        self.skip_button = QPushButton("Skip", self)
        self.merge_button = QPushButton("Merge…", self)
        self.refresh_button = QPushButton("Refresh", self)
        self.approve_button.clicked.connect(self.approve_selected)
        self.save_button.clicked.connect(self.save_selected)
        self.skip_button.clicked.connect(self.skip_selected)
        self.merge_button.clicked.connect(self.merge_selected)
        self.refresh_button.clicked.connect(self.refresh)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(self.table, 2)
        layout.addWidget(QLabel("Details", self))
        layout.addWidget(self.editor, 1)
        buttons = QHBoxLayout()
        for button in (self.approve_button, self.save_button, self.skip_button, self.merge_button, self.refresh_button):
            buttons.addWidget(button)
        buttons.addStretch()
        layout.addLayout(buttons)

    def bind(self, review_store: KnowledgeReviewStore | None) -> None:
        self.review_store = review_store
        self.refresh()

    def refresh(self) -> None:
        self.table.setRowCount(0)
        self.editor.clear()
        if self.review_store is None:
            return
        for item in self.review_store.items(self.collection):
            row = self.table.rowCount()
            self.table.insertRow(row)
            label = str(item.get("name", ""))
            if self.collection == "relationships":
                label = f"{item.get('source', '')} → {item.get('relationship', '')} → {item.get('target', '')}"
            values = [
                label,
                str(item.get("status", "pending_review")),
                "Yes" if bool(item.get("approved", False)) else "No",
                str(item.get("id", "")),
            ]
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if column == 3:
                    cell.setFlags(cell.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, column, cell)
        self.table.resizeColumnsToContents()

    def _selected_id(self) -> str:
        row = self.table.currentRow()
        if row < 0:
            return ""
        item = self.table.item(row, 3)
        return item.text().strip() if item else ""

    def _load_selected(self) -> None:
        item_id = self._selected_id()
        if not item_id or self.review_store is None:
            self.editor.clear()
            return
        try:
            item = self.review_store.get(self.collection, item_id)
        except Exception:
            self.editor.clear()
            return
        self.editor.setPlainText(json.dumps(item, ensure_ascii=False, indent=2))

    def approve_selected(self) -> None:
        item_id = self._selected_id()
        if not item_id or self.review_store is None:
            return
        self.review_store.approve(self.collection, item_id)
        self.refresh()

    def skip_selected(self) -> None:
        item_id = self._selected_id()
        if not item_id or self.review_store is None:
            return
        self.review_store.skip(self.collection, item_id)
        self.refresh()

    def save_selected(self) -> None:
        item_id = self._selected_id()
        if not item_id or self.review_store is None:
            return
        try:
            values = json.loads(self.editor.toPlainText())
            if not isinstance(values, dict):
                raise ValueError("Editor must contain one JSON object.")
            self.review_store.edit(self.collection, item_id, values)
        except Exception as exc:
            QMessageBox.warning(self, "Unable to Save", str(exc))
            return
        self.refresh()

    def merge_selected(self) -> None:
        if self.collection == "relationships":
            QMessageBox.information(self, "Merge", "Relationship merging is not needed; edit or skip the relationship instead.")
            return
        source_id = self._selected_id()
        if not source_id or self.review_store is None:
            return
        candidates = [
            item for item in self.review_store.items(self.collection)
            if str(item.get("id", "")) != source_id and str(item.get("status", "")) != "merged"
        ]
        if not candidates:
            QMessageBox.information(self, "Merge", "No other item is available to merge into.")
            return
        labels = [f"{item.get('name', item.get('id'))} [{item.get('id')}]" for item in candidates]
        choice, accepted = QInputDialog.getItem(self, "Merge Item", "Merge selected item into:", labels, 0, False)
        if not accepted:
            return
        target = candidates[labels.index(choice)]
        try:
            self.review_store.merge(self.collection, source_id, str(target.get("id", "")))
        except Exception as exc:
            QMessageBox.warning(self, "Unable to Merge", str(exc))
            return
        self.refresh()


class StoryReviewPanel(QWidget):
    """Human review surface for Story Intelligence knowledge."""

    COLLECTIONS = (
        ("characters", "Characters"),
        ("locations", "Locations"),
        ("objects", "Objects"),
        ("relationships", "Relationships"),
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = None
        self.review_store = None
        self.summary = QLabel("Open a project to review story knowledge.", self)
        self.summary.setWordWrap(True)
        self.tabs = QTabWidget(self)
        self.pages = {}
        layout = QVBoxLayout(self)
        layout.addWidget(self.summary)
        layout.addWidget(self.tabs, 1)
        for collection, title in self.COLLECTIONS:
            page = _CollectionReviewPage(collection, self)
            self.pages[collection] = page
            self.tabs.addTab(page, title)

    def set_project(self, project) -> None:
        self.project = project
        self.review_store = KnowledgeReviewStore(project.root)
        for page in self.pages.values():
            page.bind(self.review_store)
        self.refresh()

    def refresh(self) -> None:
        if self.review_store is None:
            return
        counts = self.review_store.counts()
        parts = [f"{name.title()}: {data['pending']} pending / {data['total']} total" for name, data in counts.items()]
        self.summary.setText(" • ".join(parts) + (" • Review complete" if self.review_store.review_complete() else ""))
        for page in self.pages.values():
            page.refresh()

    def clear(self) -> None:
        self.project = None
        self.review_store = None
        self.summary.setText("Open a project to review story knowledge.")
        for page in self.pages.values():
            page.bind(None)
