from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from desktop.project.project_controller import (
    ProjectController,
)

from desktop.settings import UIState

from desktop.themes.theme_manager import (
    ThemeManager,
)

from desktop.ui.main_window import (
    MainWindow,
)


class AIContentStudio:
    """
    Main desktop application bootstrap.

    Responsibilities:
    - Create QApplication
    - Load theme
    - Create MainWindow
    - Initialize controllers
    - Restore UI state
    - Save state on shutdown
    """


    def __init__(
        self,
    ):

        self.qt = QApplication(
            sys.argv
        )


        self.project_controller = None

        self.ui_state = None

        self.window = None


        self._initialize()


    # --------------------------------------------------
    # Initialization
    # --------------------------------------------------

    def _initialize(
        self,
    ):

        ThemeManager.load_dark(
            self.qt
        )


        self.window = MainWindow()


        # ------------------------------------------
        # Controllers
        # ------------------------------------------

        self.project_controller = ProjectController()


        self.window.set_project_controller(
            self.project_controller
        )


        # ------------------------------------------
        # UI State
        # ------------------------------------------

        self.ui_state = UIState()


        self._restore_state()



    # --------------------------------------------------
    # Restore
    # --------------------------------------------------

    def _restore_state(
        self,
    ):

        try:

            self.ui_state.restore_main_window(
                self.window
            )


            self.ui_state.restore_workspace(
                self.window.workspace
            )


            self.ui_state.restore_narration(
                self.window.narration_panel()
            )

        except Exception:

            pass



    # --------------------------------------------------
    # Run
    # --------------------------------------------------

    def run(
        self,
    ):

        self.window.show()


        exit_code = self.qt.exec()


        self.shutdown()


        return exit_code



    # --------------------------------------------------
    # Shutdown
    # --------------------------------------------------

    def shutdown(
        self,
    ):

        try:

            self._save_state()

        except Exception:

            pass


        try:

            if self.project_controller:

                self.project_controller.auto_save()

        except Exception:

            pass



    # --------------------------------------------------
    # Save State
    # --------------------------------------------------

    def _save_state(
        self,
    ):

        if not self.ui_state:

            return


        self.ui_state.save_workspace(
            self.window.workspace
        )


        self.ui_state.save_narration(
            self.window.narration_panel()
        )


        self.ui_state.save_main_window(
            self.window
        )