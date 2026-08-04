from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QVBoxLayout


class ImportStatistics(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

        self.pages = QLabel()

        self.text_pages = QLabel()

        self.scanned = QLabel()

        layout.addWidget(self.pages)

        layout.addWidget(self.text_pages)

        layout.addWidget(self.scanned)

    def update(self, stats):

        self.pages.setText(
            f"Pages : {stats.pages_processed}"
        )

        self.text_pages.setText(
            f"Text : {stats.text_pages}"
        )

        self.scanned.setText(
            f"Scanned : {stats.scanned_pages}"
        )