from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QVBoxLayout


class ImportSummaryDialog(QDialog):

    def __init__(self, statistics):

        super().__init__()

        self.setWindowTitle(
            "Import Complete"
        )

        layout = QVBoxLayout(self)

        layout.addWidget(
            QLabel(
                f"Pages : {statistics.pages_processed}"
            )
        )

        layout.addWidget(
            QLabel(
                f"Text Pages : {statistics.text_pages}"
            )
        )

        layout.addWidget(
            QLabel(
                f"Scanned Pages : {statistics.scanned_pages}"
            )
        )

        ok = QPushButton("OK")

        ok.clicked.connect(self.accept)

        layout.addWidget(ok)