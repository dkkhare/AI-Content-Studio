from __future__ import annotations

import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from backend.publishing import ReleaseManager


class ReleaseManagerPanel(QWidget):
    """Review publish-ready episode files and manage provider-neutral release state."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = None
        self.manager = None
        self.summary = QLabel("Open a project to manage releases.", self)
        self.summary.setWordWrap(True)
        self.table = QTableWidget(0, 7, self)
        self.table.setHorizontalHeaderLabels([
            "Episode", "Title", "State", "Ready", "Video", "Thumbnail", "ID"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self._load_selected)
        self.details = QTextEdit(self)
        self.details.setReadOnly(True)
        self.ready_button = QPushButton("Mark Ready", self)
        self.draft_button = QPushButton("Back to Draft", self)
        self.published_button = QPushButton("Mark Published", self)
        self.failed_button = QPushButton("Mark Failed", self)
        self.refresh_button = QPushButton("Refresh", self)
        self.ready_button.clicked.connect(self.mark_ready)
        self.draft_button.clicked.connect(self.mark_draft)
        self.published_button.clicked.connect(self.mark_published)
        self.failed_button.clicked.connect(self.mark_failed)
        self.refresh_button.clicked.connect(self.refresh)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(self.summary)
        layout.addWidget(self.table, 2)
        layout.addWidget(QLabel("Publish Manifest / Release History", self))
        layout.addWidget(self.details, 2)
        buttons = QHBoxLayout()
        for button in (
            self.ready_button,
            self.draft_button,
            self.published_button,
            self.failed_button,
            self.refresh_button,
        ):
            buttons.addWidget(button)
        buttons.addStretch()
        layout.addLayout(buttons)

    def set_project(self, project) -> None:
        self.project = project
        self.manager = ReleaseManager(project.root)
        self.refresh()

    def clear(self) -> None:
        self.project = None
        self.manager = None
        self.table.setRowCount(0)
        self.details.clear()
        self.summary.setText("Open a project to manage releases.")

    def refresh(self) -> None:
        self.table.setRowCount(0)
        self.details.clear()
        if self.manager is None:
            return
        summary = self.manager.summary()
        self.summary.setText(
            f"Releases: {summary['total']} total • {summary['draft']} draft • "
            f"{summary['ready']} ready • {summary['published']} published • "
            f"{summary['failed']} failed"
        )
        for item in self.manager.items():
            validation = item.get("validation", {})
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                str(item.get("episode_id", "")),
                str(item.get("title", "")),
                str(item.get("state", "draft")),
                "Yes" if validation.get("ready") else "No",
                "Yes" if validation.get("video_exists") else "No",
                "Yes" if validation.get("thumbnail_exists") else "No",
                str(item.get("episode_id", "")),
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
        item = self.table.item(row, 6)
        return item.text().strip() if item else ""

    def _load_selected(self) -> None:
        episode_id = self._selected_id()
        if not episode_id or self.manager is None:
            self.details.clear()
            return
        release = self.manager.get(episode_id)
        validation = self.manager.validation(episode_id)
        try:
            manifest = self.manager.manifest(episode_id)
        except Exception as exc:
            manifest = {"error": str(exc)}
        payload = {
            "validation": validation,
            "release": release,
            "manifest": manifest,
        }
        self.details.setPlainText(json.dumps(payload, ensure_ascii=False, indent=2))

    def _run(self, action) -> None:
        episode_id = self._selected_id()
        if not episode_id or self.manager is None:
            return
        try:
            action(episode_id)
        except Exception as exc:
            QMessageBox.warning(self, "Release Manager", str(exc))
            return
        self.refresh()

    def mark_ready(self) -> None:
        self._run(lambda episode_id: self.manager.mark_ready(episode_id))

    def mark_draft(self) -> None:
        self._run(lambda episode_id: self.manager.mark_draft(episode_id))

    def mark_failed(self) -> None:
        episode_id = self._selected_id()
        if not episode_id or self.manager is None:
            return
        error, accepted = QInputDialog.getText(self, "Mark Release Failed", "Error / reason")
        if not accepted or not error.strip():
            return
        self._run(lambda selected: self.manager.mark_failed(selected, error.strip()))

    def mark_published(self) -> None:
        episode_id = self._selected_id()
        if not episode_id or self.manager is None:
            return
        destination, accepted = QInputDialog.getText(
            self, "Mark Published", "Destination (for example YouTube or Podcast RSS)"
        )
        if not accepted or not destination.strip():
            return
        external_url, _ = QInputDialog.getText(
            self, "Published URL", "External URL (optional)"
        )
        self._run(
            lambda selected: self.manager.mark_published(
                selected,
                destination=destination.strip(),
                external_url=external_url.strip(),
            )
        )
