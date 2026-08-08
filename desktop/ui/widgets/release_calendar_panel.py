from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from backend.publishing import ReleaseCalendarService


class ReleaseCalendarPanel(QWidget):
    """Preview and apply a reusable book/channel release cadence."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = None
        self.service = None

        self.name = QLineEdit(self)
        self.timezone = QLineEdit(self)
        self.start_date = QLineEdit(self)
        self.local_time = QLineEdit(self)
        self.interval_days = QSpinBox(self)
        self.interval_days.setRange(1, 365)
        self.weekdays = QLineEdit(self)
        self.playlist_id = QLineEdit(self)
        self.ready_only = QCheckBox("Schedule Ready episodes only", self)

        self.preview_button = QPushButton("Preview Calendar", self)
        self.save_button = QPushButton("Save Preset", self)
        self.apply_button = QPushButton("Apply Calendar", self)
        self.refresh_button = QPushButton("Refresh", self)
        self.preview_button.clicked.connect(self.preview)
        self.save_button.clicked.connect(self.save_preset)
        self.apply_button.clicked.connect(self.apply_calendar)
        self.refresh_button.clicked.connect(self.refresh)

        self.status = QLabel("Open a project to configure a release calendar.", self)
        self.status.setWordWrap(True)
        self.table = QTableWidget(0, 7, self)
        self.table.setHorizontalHeaderLabels([
            "Episode", "#", "Title", "Local Publish Time", "UTC / YouTube", "Timezone", "Playlist"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        box = QGroupBox("Channel / Book Publishing Preset", self)
        form = QFormLayout(box)
        form.addRow("Preset name", self.name)
        form.addRow("Timezone (IANA)", self.timezone)
        form.addRow("Start date (YYYY-MM-DD)", self.start_date)
        form.addRow("Local publish time (HH:MM)", self.local_time)
        form.addRow("Every N days", self.interval_days)
        form.addRow("Weekdays (optional: Mon,Wed,Fri)", self.weekdays)
        form.addRow("YouTube playlist ID", self.playlist_id)
        form.addRow(self.ready_only)
        layout.addWidget(box)

        buttons = QHBoxLayout()
        for button in (self.preview_button, self.save_button, self.apply_button, self.refresh_button):
            buttons.addWidget(button)
        buttons.addStretch()
        layout.addLayout(buttons)
        layout.addWidget(self.status)
        layout.addWidget(self.table, 1)

    def set_project(self, project) -> None:
        self.project = project
        self.service = ReleaseCalendarService(project)
        self._load_preset()
        self.preview()

    def clear(self) -> None:
        self.project = None
        self.service = None
        self.table.setRowCount(0)
        self.status.setText("Open a project to configure a release calendar.")

    def _load_preset(self) -> None:
        if self.service is None:
            return
        preset = self.service.preset()
        self.name.setText(str(preset.get("name", "Default Release Calendar")))
        self.timezone.setText(str(preset.get("timezone", "Asia/Kolkata")))
        self.start_date.setText(str(preset.get("start_date", date.today().isoformat())))
        self.local_time.setText(str(preset.get("local_time", "18:00")))
        self.interval_days.setValue(int(preset.get("interval_days", 1) or 1))
        self.weekdays.setText(",".join(str(v) for v in preset.get("weekdays", [])))
        self.playlist_id.setText(str(preset.get("playlist_id", "")))
        self.ready_only.setChecked(bool(preset.get("ready_only", True)))

    def _preset_from_form(self) -> dict:
        return {
            "name": self.name.text().strip() or "Default Release Calendar",
            "timezone": self.timezone.text().strip() or "Asia/Kolkata",
            "start_date": self.start_date.text().strip(),
            "local_time": self.local_time.text().strip() or "18:00",
            "interval_days": int(self.interval_days.value()),
            "weekdays": self.weekdays.text().strip(),
            "playlist_id": self.playlist_id.text().strip(),
            "ready_only": self.ready_only.isChecked(),
        }

    def _show_rows(self, rows: list[dict]) -> None:
        self.table.setRowCount(0)
        for item in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                str(item.get("episode_id", "")),
                str(item.get("episode_number", "")),
                str(item.get("title", "")),
                str(item.get("local_publish_at", "")),
                str(item.get("scheduled_publish_at", "")),
                str(item.get("timezone", "")),
                str(item.get("playlist_id", "")),
            ]
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                cell.setFlags(cell.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, column, cell)
        self.table.resizeColumnsToContents()

    def preview(self) -> None:
        if self.service is None:
            return
        try:
            rows = self.service.preview(self._preset_from_form())
        except Exception as exc:
            QMessageBox.warning(self, "Release Calendar", str(exc))
            return
        self._show_rows(rows)
        self.status.setText(
            f"Preview only: {len(rows)} episode(s) would be scheduled. No release records were changed."
        )

    def save_preset(self) -> None:
        if self.service is None:
            return
        try:
            preset = self.service.save_preset(self._preset_from_form())
        except Exception as exc:
            QMessageBox.warning(self, "Release Calendar", str(exc))
            return
        self.status.setText(f"Saved publishing preset: {preset['name']}")
        self.preview()

    def apply_calendar(self) -> None:
        if self.service is None:
            return
        try:
            rows = self.service.apply(self._preset_from_form())
        except Exception as exc:
            QMessageBox.warning(self, "Release Calendar", str(exc))
            return
        self._show_rows(rows)
        self.status.setText(
            f"Applied schedule and playlist to {len(rows)} episode(s). Review them in Release Manager before bulk publishing."
        )

    def refresh(self) -> None:
        if self.service is None:
            return
        self._load_preset()
        self.preview()
