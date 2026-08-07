from __future__ import annotations

import sys
from pathlib import Path

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

        self.pipeline_controller.jobSubmitted.connect(self._on_processing_job_submitted)
        self.pipeline_controller.jobFinished.connect(self._on_processing_job_finished)
        self.pipeline_controller.queueRecoveryError.connect(
            lambda message: self.window.log(f"Processing queue recovery: {message}")
        )

        self.ui_state = UIState()
        self._restore_state()
        self._recover_processing_queue()

    def _on_processing_job_submitted(self, record) -> None:
        if self.window is None:
            return
        root = str(record.get("project_root", ""))
        name = Path(root).name if root else "project"
        self.window.log(f"Processing queued: {name}")
        self.window.outputDock.append(f"QUEUED: {name}")

    def _on_processing_job_finished(self, record) -> None:
        if self.window is None:
            return

        root = str(record.get("project_root", ""))
        name = Path(root).name if root else "project"
        status = str(record.get("status", "completed"))
        error = str(record.get("error", "") or "")

        if status == "completed":
            message = f"Processing completed: {name}"
            self.window.outputDock.show_success(message)
        elif status == "cancelled":
            message = f"Processing cancelled: {name}"
            self.window.outputDock.append(f"CANCELLED: {name}")
        else:
            message = f"Processing failed: {name}"
            if error:
                message = f"{message} — {error}"
            self.window.outputDock.show_error(message)

        self.window.log(message)
        self.window.statusBar().showMessage(message, 5000)

        current_root = None
        if self.project_controller is not None:
            current_root = self.project_controller.project_root()
        if root and current_root is not None:
            try:
                if Path(root).resolve() == Path(current_root).resolve():
                    self.window.projectDock.refresh(current_root)
                    self.window.workspace.refresh()
            except Exception:
                pass

    def _recover_processing_queue(self) -> None:
        if self.pipeline_controller is None:
            return
        try:
            recovered = self.pipeline_controller.recover_pending_jobs()
            if recovered and self.window is not None:
                self.window.log(f"Recovered {recovered} queued processing job(s).")
        except Exception as exc:
            if self.window is not None:
                self.window.log(f"Processing queue recovery failed: {exc}")

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

        if self.pipeline_controller is not None:
            if self.pipeline_controller.running:
                try:
                    self.pipeline_controller.cancel()
                    self.pipeline_controller.wait(5.0)
                except Exception:
                    pass
            try:
                self.pipeline_controller.shutdown_queue(
                    cancel_current=True,
                    wait=5.0,
                )
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
