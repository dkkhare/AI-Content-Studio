from PySide6.QtWidgets import QApplication
import sys

from desktop.themes.theme_manager import ThemeManager
from desktop.ui.main_window import MainWindow


class AIContentStudio:

    def __init__(self):

        self.qt = QApplication(sys.argv)

        ThemeManager.load_dark(self.qt)

        self.window = MainWindow()

    def run(self):

        self.window.show()

        return self.qt.exec()