from PySide6.QtWidgets import QApplication
import sys

from desktop.ui.main_window import MainWindow


class AIContentStudio:

    def __init__(self):

        self.qt = QApplication(sys.argv)

        self.window = MainWindow()

    def run(self):

        self.window.show()

        return self.qt.exec()