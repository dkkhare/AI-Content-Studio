from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QHBoxLayout


class PageNavigation(QWidget):

    def __init__(self):

        super().__init__()

        layout = QHBoxLayout(self)

        self.previous = QPushButton("<")

        self.next = QPushButton(">")

        self.page = QLabel("1 / 1")

        layout.addWidget(self.previous)

        layout.addWidget(self.page)

        layout.addWidget(self.next)