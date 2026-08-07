from __future__ import annotations

import json

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from backend.scenes import SceneReviewStore


class SceneReviewPanel(QWidget):
    """Review generated scene plans before image/video generation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = None
        self.store = None
        self.summary = QLabel("Open a project to review scenes.", self)
        self.summary.setWordWrap(True)
        self.table = QTableWidget(0, 6, self)
        self.table.setHorizontalHeaderLabels(["Episode", "#", "Summary", "Duration", "Status", "ID"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self._load_selected)
        self.editor = QTextEdit(self)
        self.editor.setPlaceholderText("Selected scene JSON. Edit visual/camera/prompt fields, then Save Edit.")
        self.approve_button = QPushButton("Approve", self)
        self.save_button = QPushButton("Save Edit", self)
        self.skip_button = QPushButton("Skip", self)
        self.refresh_button = QPushButton("Refresh", self)
        self.approve_button.clicked.connect(self.approve_selected)
        self.save_button.clicked.connect(self.save_selected)
        self.skip_button.clicked.connect(self.skip_selected)
        self.refresh_button.clicked.connect(self.refresh)
        layout = QVBoxLayout(self)
        layout.addWidget(self.summary)
        layout.addWidget(self.table, 2)
        layout.addWidget(QLabel("Scene Details", self))
        layout.addWidget(self.editor, 1)
        buttons = QHBoxLayout()
        for button in (self.approve_button, self.save_button, self.skip_button, self.refresh_button):
            buttons.addWidget(button)
        buttons.addStretch()
        layout.addLayout(buttons)

    def set_project(self, project) -> None:
        self.project = project
        self.store = SceneReviewStore(project.root)
        self.refresh()

    def clear(self) -> None:
        self.project = None
        self.store = None
        self.summary.setText("Open a project to review scenes.")
        self.table.setRowCount(0)
        self.editor.clear()

    def refresh(self) -> None:
        self.table.setRowCount(0)
        self.editor.clear()
        if self.store is None:
            return
        counts = self.store.counts()
        self.summary.setText(
            f"Scenes: {counts['total']} total • {counts['approved']} approved • "
            f"{counts['skipped']} skipped • {counts['pending']} pending"
            + (" • Review complete" if counts['total'] and counts['pending'] == 0 else "")
        )
        for scene in self.store.scenes():
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                str(scene.get("episode_id", "")),
                str(scene.get("sequence", "")),
                str(scene.get("summary", scene.get("visual_description", ""))),
                str(scene.get("estimated_seconds", "")),
                str(scene.get("status", "planned")),
                str(scene.get("id", "")),
            ]
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))
        self.table.resizeColumnsToContents()

    def _selected_id(self) -> str:
        row = self.table.currentRow()
        if row < 0:
            return ""
        item = self.table.item(row, 5)
        return item.text().strip() if item else ""

    def _load_selected(self) -> None:
        scene_id = self._selected_id()
        if not scene_id or self.store is None:
            self.editor.clear()
            return
        try:
            self.editor.setPlainText(json.dumps(self.store.get(scene_id), ensure_ascii=False, indent=2))
        except Exception:
            self.editor.clear()

    def approve_selected(self) -> None:
        scene_id = self._selected_id()
        if scene_id and self.store is not None:
            self.store.approve(scene_id)
            self.refresh()

    def skip_selected(self) -> None:
        scene_id = self._selected_id()
        if scene_id and self.store is not None:
            self.store.skip(scene_id)
            self.refresh()

    def save_selected(self) -> None:
        scene_id = self._selected_id()
        if not scene_id or self.store is None:
            return
        try:
            values = json.loads(self.editor.toPlainText())
            if not isinstance(values, dict):
                raise ValueError("Editor must contain one JSON object.")
            self.store.edit(scene_id, values)
        except Exception as exc:
            QMessageBox.warning(self, "Unable to Save Scene", str(exc))
            return
        self.refresh()
