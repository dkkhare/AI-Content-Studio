import sys

from PySide6.QtWidgets import QApplication

from desktop.settings import UIState
from desktop.themes.theme_manager import ThemeManager
from desktop.ui.main_window import MainWindow


class AIContentStudio:

    def __init__(self):

        self.qt = QApplication(sys.argv)

        ThemeManager.load_dark(self.qt)

        self.window = MainWindow()

        self.ui_state = UIState()

        # ------------------------------------------
        # Restore previous application state
        # ------------------------------------------

        self.ui_state.restore_main_window(
            self.window
        )

        self.ui_state.restore_workspace(
            self.window.workspace
        )

        self.ui_state.restore_narration(
            self.window.narration_panel()
        )

    def run(self):

        self.window.show()

        exit_code = self.qt.exec()

        # ------------------------------------------
        # Save application state before exit
        # ------------------------------------------

        self.ui_state.save_workspace(
            self.window.workspace
        )

        self.ui_state.save_narration(
            self.window.narration_panel()
        )

        self.ui_state.save_main_window(
            self.window
        )

        return exit_code