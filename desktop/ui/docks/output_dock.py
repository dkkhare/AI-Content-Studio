from PySide6.QtWidgets import (
    QDockWidget,
    QTextEdit,
)


class OutputDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Output", parent)

        viewer = QTextEdit()
        viewer.setReadOnly(True)

        self.setWidget(viewer)

        self.viewer = viewer

    def append(self, text: str):
        self.viewer.append(text)