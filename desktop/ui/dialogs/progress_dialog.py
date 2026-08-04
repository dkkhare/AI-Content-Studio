from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QProgressBar,
)


class ProgressDialog(QDialog):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "Importing PDF"
        )

        layout = QVBoxLayout(self)

        self.label = QLabel()

        self.progress = QProgressBar()

        layout.addWidget(self.label)

        layout.addWidget(self.progress)

    def update_progress(self, progress):

        self.progress.setValue(progress.percent)

        self.label.setText(

            f"Page {progress.current_page}/{progress.total_pages}"

        )