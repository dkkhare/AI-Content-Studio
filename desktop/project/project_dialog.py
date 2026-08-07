from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PySide6.QtWidgets import (
    QFileDialog,
    QInputDialog,
    QMessageBox,
)


class ProjectDialogs:
    """Dialog helpers for project lifecycle actions."""

    @staticmethod
    def new_project(parent):
        name, ok = QInputDialog.getText(
            parent,
            "New Project",
            "Project name:",
        )

        if not ok or not name.strip():
            return None

        directory = QFileDialog.getExistingDirectory(
            parent,
            "Choose Project Location",
        )

        if not directory:
            return None

        name = name.strip()
        return name, Path(directory) / name

    @staticmethod
    def open_project(parent):
        directory = QFileDialog.getExistingDirectory(
            parent,
            "Open Project",
        )

        if not directory:
            return None

        return Path(directory)

    @staticmethod
    def save_project_as(parent):
        directory = QFileDialog.getExistingDirectory(
            parent,
            "Save Project As",
        )

        if not directory:
            return None

        return Path(directory)

    @staticmethod
    def confirm_close(parent) -> str:
        """Return one of: 'save', 'discard', or 'cancel'."""
        result = QMessageBox.warning(
            parent,
            "Unsaved Changes",
            "This project has unsaved changes. Save before closing?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save,
        )

        if result == QMessageBox.Save:
            return "save"
        if result == QMessageBox.Discard:
            return "discard"
        return "cancel"

    @staticmethod
    def confirm_recovery(parent, recovery_file: str | Path) -> str:
        """Return one of: 'recover', 'discard', or 'later'."""
        recovery_file = Path(recovery_file)

        box = QMessageBox(parent)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle("Project Recovery Available")
        box.setText(
            "A recovery snapshot was found for this project."
        )
        box.setInformativeText(
            f"Recovery file:\n{recovery_file}\n\n"
            "Recover it now, discard it, or keep it for later?"
        )

        recover_button = box.addButton("Recover", QMessageBox.AcceptRole)
        discard_button = box.addButton("Discard Recovery", QMessageBox.DestructiveRole)
        later_button = box.addButton("Keep for Later", QMessageBox.RejectRole)
        box.setDefaultButton(recover_button)
        box.exec()

        clicked = box.clickedButton()
        if clicked is recover_button:
            return "recover"
        if clicked is discard_button:
            return "discard"
        if clicked is later_button:
            return "later"
        return "later"

    @staticmethod
    def choose_backup(
        parent,
        backups: Iterable[str | Path],
        title: str = "Select Backup",
    ) -> Path | None:
        paths = [Path(item) for item in backups]
        if not paths:
            QMessageBox.information(
                parent,
                title,
                "No project backups are available.",
            )
            return None

        labels = [path.name for path in paths]
        selected, ok = QInputDialog.getItem(
            parent,
            title,
            "Backup:",
            labels,
            0,
            False,
        )

        if not ok or not selected:
            return None

        return paths[labels.index(selected)]

    @staticmethod
    def confirm_restore_backup(parent, backup: str | Path) -> bool:
        backup = Path(backup)
        result = QMessageBox.warning(
            parent,
            "Restore Backup",
            f"Restore backup '{backup.name}'?\n\n"
            "A safety backup of the current project will be created first.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return result == QMessageBox.Yes

    @staticmethod
    def confirm_delete_backup(parent, backup: str | Path) -> bool:
        backup = Path(backup)
        result = QMessageBox.warning(
            parent,
            "Delete Backup",
            f"Permanently delete backup '{backup.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return result == QMessageBox.Yes

    @staticmethod
    def backup_cleanup_count(parent, current_count: int) -> int | None:
        keep, ok = QInputDialog.getInt(
            parent,
            "Cleanup Backups",
            f"There are {current_count} backup(s). Keep newest:",
            min(10, current_count) if current_count else 0,
            0,
            max(0, current_count),
            1,
        )

        if not ok:
            return None

        return keep

    # Compatibility aliases for older callers.
    create_project = new_project
    save_as_project = save_project_as
