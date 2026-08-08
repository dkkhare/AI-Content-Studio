from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from backend.readiness import ReadinessService


class ReadinessPanel(QWidget):
    """Run local dependency checks and show actionable blockers/warnings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = None
        self.summary = QLabel("Open a project to check setup readiness.", self)
        self.summary.setWordWrap(True)
        self.table = QTableWidget(0, 5, self)
        self.table.setHorizontalHeaderLabels(["Check", "Status", "Required", "Detail", "Fix hint"])
        self.run_button = QPushButton("Run Readiness Check", self)
        self.run_button.clicked.connect(self.refresh)
        layout = QVBoxLayout(self)
        layout.addWidget(self.summary)
        layout.addWidget(self.run_button)
        layout.addWidget(self.table)

    def set_project(self, project) -> None:
        self.project = project
        self.refresh()

    def clear(self) -> None:
        self.project = None
        self.table.setRowCount(0)
        self.summary.setText("Open a project to check setup readiness.")

    def refresh(self) -> None:
        self.table.setRowCount(0)
        if self.project is None:
            return
        report = ReadinessService(self.project).run()
        if report.get("ready"):
            self.summary.setText(
                f"READY • 0 blockers • {report.get('warning_count', 0)} optional warning(s). "
                "The required local pipeline dependencies are available."
            )
        else:
            self.summary.setText(
                f"NOT READY • {report.get('blocker_count', 0)} blocker(s) • "
                f"{report.get('warning_count', 0)} optional warning(s). Fix required items before full production."
            )
        for check in report.get("checks", []):
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                str(check.get("label", "")),
                "OK" if check.get("ok") else ("BLOCKED" if check.get("required") else "WARNING"),
                "Yes" if check.get("required") else "No",
                str(check.get("detail", "")),
                str(check.get("hint", "")),
            ]
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                cell.setFlags(cell.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, column, cell)
        self.table.resizeColumnsToContents()
