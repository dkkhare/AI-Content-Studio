from __future__ import annotations

import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from backend.publishing import PublishingService, ReleaseManager


class ReleaseManagerPanel(QWidget):
    """Review publish-ready episodes and publish them through pluggable providers."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = None
        self.manager = None
        self.publisher = None
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

        self.provider_combo = QComboBox(self)
        self.youtube_client_secrets = QLineEdit(self)
        self.youtube_token_path = QLineEdit(self)
        self.save_provider_button = QPushButton("Save Publishing Settings", self)
        self.publish_button = QPushButton("Publish Ready Episode", self)
        self.save_provider_button.clicked.connect(self.save_provider_settings)
        self.publish_button.clicked.connect(self.publish_selected)

        self.ready_button = QPushButton("Mark Ready", self)
        self.draft_button = QPushButton("Back to Draft", self)
        self.published_button = QPushButton("Mark Published Manually", self)
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

        provider_box = QGroupBox("Publishing Provider", self)
        provider_form = QFormLayout(provider_box)
        provider_form.addRow("Provider", self.provider_combo)
        provider_form.addRow("YouTube OAuth client-secrets JSON", self.youtube_client_secrets)
        provider_form.addRow("YouTube OAuth token JSON", self.youtube_token_path)
        provider_buttons = QHBoxLayout()
        provider_buttons.addWidget(self.save_provider_button)
        provider_buttons.addWidget(self.publish_button)
        provider_buttons.addStretch()
        provider_form.addRow(provider_buttons)
        layout.addWidget(provider_box)

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
        self._load_provider_settings()
        self._rebuild_publisher()
        self.refresh()

    def _load_provider_settings(self) -> None:
        if self.project is None:
            return
        self.youtube_client_secrets.setText(str(self.project.get_setting("youtube_client_secrets_path", "") or ""))
        self.youtube_token_path.setText(str(self.project.get_setting("youtube_token_path", "") or ""))
        preferred = str(self.project.get_setting("publishing_provider", "manual") or "manual")
        self.provider_combo.clear()
        self.provider_combo.addItem("Manual / External", "manual")
        self.provider_combo.addItem("YouTube", "youtube")
        index = self.provider_combo.findData(preferred)
        self.provider_combo.setCurrentIndex(index if index >= 0 else 0)

    def _rebuild_publisher(self) -> None:
        self.publisher = PublishingService(self.project) if self.project is not None else None

    def save_provider_settings(self) -> None:
        if self.project is None:
            return
        self.project.update_settings({
            "publishing_provider": str(self.provider_combo.currentData() or "manual"),
            "youtube_client_secrets_path": self.youtube_client_secrets.text().strip(),
            "youtube_token_path": self.youtube_token_path.text().strip(),
        })
        self._rebuild_publisher()
        self.refresh()

    def clear(self) -> None:
        self.project = None
        self.manager = None
        self.publisher = None
        self.table.setRowCount(0)
        self.details.clear()
        self.provider_combo.clear()
        self.youtube_client_secrets.clear()
        self.youtube_token_path.clear()
        self.summary.setText("Open a project to manage releases.")

    def refresh(self) -> None:
        self.table.setRowCount(0)
        self.details.clear()
        if self.manager is None:
            return
        summary = self.manager.summary()
        provider_text = ""
        if self.publisher is not None:
            statuses = {item["id"]: item for item in self.publisher.provider_status()}
            selected = str(self.provider_combo.currentData() or "manual")
            status = statuses.get(selected, {})
            provider_text = f" • Provider: {status.get('name', selected)} ({'configured' if status.get('configured') else 'not configured'})"
        self.summary.setText(
            f"Releases: {summary['total']} total • {summary['draft']} draft • "
            f"{summary['ready']} ready • {summary['published']} published • "
            f"{summary['failed']} failed{provider_text}"
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

    def publish_selected(self) -> None:
        episode_id = self._selected_id()
        if not episode_id or self.publisher is None:
            return
        provider_id = str(self.provider_combo.currentData() or "manual")
        if provider_id == "manual":
            QMessageBox.information(
                self,
                "Manual Publishing",
                "Publish the episode externally, then use Mark Published Manually to record the destination and URL.",
            )
            return
        try:
            self.publisher.publish_episode(episode_id, provider_id)
        except Exception as exc:
            QMessageBox.warning(self, "Publishing Failed", str(exc))
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
        external_url, _ = QInputDialog.getText(self, "Published URL", "External URL (optional)")
        self._run(
            lambda selected: self.manager.mark_published(
                selected,
                destination=destination.strip(),
                external_url=external_url.strip(),
            )
        )
