import sys

from PySide6.QtWidgets import QApplication

from desktop.project.project_controller import (
    ProjectController,
)

from desktop.settings import UIState
from desktop.themes.theme_manager import ThemeManager
from desktop.ui.main_window import MainWindow


class AIContentStudio:

    def __init__(self):

        self.qt = QApplication(sys.argv)

        ThemeManager.load_dark(self.qt)

        self.window = MainWindow()

        # ------------------------------------------
        # Project Controller
        # ------------------------------------------

        self.project_controller = ProjectController()

        self.window.set_project_controller(
            self.project_controller
        )

        # ------------------------------------------
        # UI State
        # ------------------------------------------

        self.ui_state = UIState()

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
        # Save UI State
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

        # ------------------------------------------
        # Auto Save Project
        # ------------------------------------------

        self.project_controller.auto_save()

        return exit_code