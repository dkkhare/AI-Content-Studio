from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


class BackupManagerDialog(QDialog):
    """Browse and manage backups for the current project."""

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller

        self.setWindowTitle("Project Backups")
        self.resize(760, 420)

        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 3, self)
        self.table.setHorizontalHeaderLabels(["Backup", "Modified", "Size"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        buttons = QHBoxLayout()
        self.create_button = QPushButton("Create Backup", self)
        self.restore_button = QPushButton("Restore", self)
        self.delete_button = QPushButton("Delete", self)
        self.cleanup_button = QPushButton("Cleanup", self)
        self.close_button = QPushButton("Close", self)

        for button in (
            self.create_button,
            self.restore_button,
            self.delete_button,
            self.cleanup_button,
        ):
            buttons.addWidget(button)
        buttons.addStretch(1)
        buttons.addWidget(self.close_button)
        layout.addLayout(buttons)

        self.create_button.clicked.connect(self.create_backup)
        self.restore_button.clicked.connect(self.restore_selected)
        self.delete_button.clicked.connect(self.delete_selected)
        self.cleanup_button.clicked.connect(self.cleanup_backups)
        self.close_button.clicked.connect(self.accept)

        self.refresh()

    def refresh(self) -> None:
        backups = self.controller.list_backups()
        self.table.setRowCount(0)

        for backup in backups:
            path = Path(backup)
            try:
                stat = path.stat()
                modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                size = self._format_size(stat.st_size)
            except OSError:
                modified = "Unavailable"
                size = "Unavailable"

            row = self.table.rowCount()
            self.table.insertRow(row)

            name_item = QTableWidgetItem(path.name)
            name_item.setData(Qt.UserRole, str(path))
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, QTableWidgetItem(modified))
            self.table.setItem(row, 2, QTableWidgetItem(size))

        has_rows = self.table.rowCount() > 0
        self.restore_button.setEnabled(has_rows)
        self.delete_button.setEnabled(has_rows)
        self.cleanup_button.setEnabled(has_rows)

    def selected_backup(self) -> Path | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if item is None:
            return None
        value = item.data(Qt.UserRole)
        return Path(value) if value else None

    def create_backup(self) -> None:
        try:
            self.controller.create_backup()
            self.refresh()
        except Exception as exc:
            QMessageBox.critical(self, "Backup Failed", str(exc))

    def restore_selected(self) -> None:
        backup = self.selected_backup()
        if backup is None:
            return

        result = QMessageBox.question(
            self,
            "Restore Backup",
            f"Restore '{backup.name}'? A safety backup will be created first.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if result != QMessageBox.Yes:
            return

        try:
            if self.controller.restore_backup(backup):
                self.refresh()
                QMessageBox.information(self, "Backup Restored", "Project backup restored successfully.")
        except Exception as exc:
            QMessageBox.critical(self, "Restore Failed", str(exc))

    def delete_selected(self) -> None:
        backup = self.selected_backup()
        if backup is None:
            return

        result = QMessageBox.question(
            self,
            "Delete Backup",
            f"Permanently delete '{backup.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if result != QMessageBox.Yes:
            return

        try:
            self.controller.delete_backup(backup)
            self.refresh()
        except Exception as exc:
            QMessageBox.critical(self, "Delete Failed", str(exc))

    def cleanup_backups(self) -> None:
        project = self.controller.project
        keep = 10
        if project is not None:
            keep = int(project.get_setting("backup_retention", 10))

        try:
            removed = self.controller.cleanup_backups(keep=keep)
            self.refresh()
            QMessageBox.information(
                self,
                "Backup Cleanup",
                f"Removed {removed} old backup(s). Keeping the newest {keep}.",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Cleanup Failed", str(exc))

    @staticmethod
    def _format_size(size: int) -> str:
        value = float(size)
        for unit in ("B", "KB", "MB", "GB"):
            if value < 1024 or unit == "GB":
                return f"{value:.1f} {unit}"
            value /= 1024
        return f"{value:.1f} GB"
