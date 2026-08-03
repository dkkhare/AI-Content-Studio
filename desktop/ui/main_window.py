from PySide6.QtWidgets import (
    QMainWindow,
    QLabel,
    QWidget,
    QVBoxLayout
)

from desktop.ui.menu_bar import build_menu
from desktop.ui.tool_bar import build_toolbar
from desktop.ui.status_bar import build_statusbar


class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("AI Content Studio")

        self.resize(1400, 900)

        build_menu(self)

        build_toolbar(self)

        build_statusbar(self)

        central = QWidget()

        layout = QVBoxLayout(central)

        title = QLabel("Welcome to AI Content Studio")

        title.setStyleSheet(
            "font-size:24px;font-weight:bold;"
        )

        layout.addStretch()

        layout.addWidget(title)

        layout.addStretch()

        self.setCentralWidget(central)