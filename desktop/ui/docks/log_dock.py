from PySide6.QtWidgets import (
    QDockWidget,
    QTextEdit,
)


class LogDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Log Console", parent)

        console = QTextEdit()
        console.setReadOnly(True)

        self.setWidget(console)

        self.console = console

    def log(self, message: str):
        self.console.append(message)