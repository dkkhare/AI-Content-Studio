from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class RecoveryDialog(QDialog):
    """Dedicated recovery wizard for autosave snapshots."""

    def __init__(self, recovery_file: str | Path, parent=None):
        super().__init__(parent)
        self.recovery_file = Path(recovery_file)
        self.choice = "later"

        self.setWindowTitle("Project Recovery")
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("A recovery snapshot was found for this project."))
        layout.addWidget(
            QLabel(
                f"Recovery file:\n{self.recovery_file}\n\n"
                "Recover the autosaved state, discard the snapshot, "
                "or keep it for later."
            )
        )

        buttons = QDialogButtonBox(self)
        recover = QPushButton("Recover", self)
        discard = QPushButton("Discard Recovery", self)
        later = QPushButton("Keep for Later", self)

        buttons.addButton(recover, QDialogButtonBox.AcceptRole)
        buttons.addButton(discard, QDialogButtonBox.DestructiveRole)
        buttons.addButton(later, QDialogButtonBox.RejectRole)
        layout.addWidget(buttons)

        recover.clicked.connect(self._recover)
        discard.clicked.connect(self._discard)
        later.clicked.connect(self._later)

    def _recover(self) -> None:
        self.choice = "recover"
        self.accept()

    def _discard(self) -> None:
        self.choice = "discard"
        self.accept()

    def _later(self) -> None:
        self.choice = "later"
        self.reject()

    @classmethod
    def ask(cls, recovery_file: str | Path, parent=None) -> str:
        dialog = cls(recovery_file, parent)
        dialog.exec()
        return dialog.choice
