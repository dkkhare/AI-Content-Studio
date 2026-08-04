from PySide6.QtWidgets import QLabel


class LoadingOverlay(QLabel):

    def __init__(self):

        super().__init__("Importing PDF...")

        self.hide()