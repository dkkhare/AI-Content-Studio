from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from desktop.controllers.pipeline_controller import PipelineController
from desktop.controllers.project_controller import ProjectController
from desktop.settings import UIState
from desktop.themes.theme_manager import ThemeManager
from desktop.ui.main_window import MainWindow


class AIContentStudio:
    """Main desktop application bootstrap."""

    def __init__(self):
        self.qt = QApplication(sys.argv)
        self.project_controller: ProjectController | None = None
        self.pipeline_controller: PipelineController | None = None
        self.ui_state: UIState | None = None
        self.window: MainWindow | None = None
        self._initialize()

    def _initialize(self) -> None:
        ThemeManager.load_dark(self.qt)

        self.window = MainWindow()
        self.project_controller = ProjectController()
        self.pipeline_controller = PipelineController()

        self.window.set_project_controller(self.project_controller)
        self.window.workspace.set_pipeline_controller(self.pipeline_controller)

        self.project_controller.projectOpened.connect(
            lambda root: self.window.workspace.open_project(self.project_controller.project)
        )
        self.project_controller.projectClosed.connect(self.window.workspace.close_project)
        self.project_controller.projectRecovered.connect(
            lambda root: self.window.workspace.open_project(self.project_controller.project)
        )
        self.project_controller.projectBackupRestored.connect(
            lambda root: self.window.workspace.open_project(self.project_controller.project)
        )

        self.ui_state = UIState()
        self._restore_state()

    def _restore_state(self) -> None:
        if self.ui_state is None or self.window is None:
            return
        try:
            self.ui_state.restore_main_window(self.window)
            self.ui_state.restore_workspace(self.window.workspace)
            narration = self.window.narration_panel() if hasattr(self.window, "narration_panel") else None
            if narration is not None:
                self.ui_state.restore_narration(narration)
        except Exception:
            pass

    def run(self) -> int:
        if self.window is None:
            return 1
        self.window.show()
        exit_code = self.qt.exec()
        self.shutdown()
        return exit_code

    def shutdown(self) -> None:
        try:
            self._save_state()
        except Exception:
            pass

        if self.pipeline_controller is not None and self.pipeline_controller.running:
            try:
                self.pipeline_controller.cancel()
                self.pipeline_controller.wait(5.0)
            except Exception:
                pass

        if self.project_controller is not None:
            try:
                self.project_controller.auto_save()
            except Exception:
                pass
            try:
                self.project_controller.dispose()
            except Exception:
                pass

    def _save_state(self) -> None:
        if self.ui_state is None or self.window is None:
            return
        self.ui_state.save_workspace(self.window.workspace)
        narration = self.window.narration_panel() if hasattr(self.window, "narration_panel") else None
        if narration is not None:
            self.ui_state.save_narration(narration)
        self.ui_state.save_main_window(self.window)
