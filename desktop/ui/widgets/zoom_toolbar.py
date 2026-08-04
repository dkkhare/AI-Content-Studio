from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QHBoxLayout


class ZoomToolbar(QWidget):

    def __init__(self):

        super().__init__()

        layout = QHBoxLayout(self)

        self.zoom_in = QPushButton("+")

        self.zoom_out = QPushButton("-")

        self.fit_page = QPushButton("Fit")

        layout.addWidget(self.zoom_out)

        layout.addWidget(self.zoom_in)

        layout.addWidget(self.fit_page)