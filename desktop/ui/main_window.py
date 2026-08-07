from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QMessageBox

from desktop.controllers.project_controller import ProjectController
from desktop.project.project_dialog import ProjectDialogs
from desktop.settings import RecentProjects, UIState
from desktop.ui.dashboard import Dashboard
from desktop.ui.docks.log_dock import LogDock
from desktop.ui.docks.output_dock import OutputDock
from desktop.ui.docks.project_dock import ProjectDock
from desktop.ui.menu_bar import build_menu
from desktop.ui.status_bar import build_statusbar
from desktop.ui.tool_bar import build_toolbar
from desktop.ui.workspace import Workspace


class MainWindow(QMainWindow):
    """Main application window with Milestone 11 project lifecycle wiring."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AI Content Studio")
        self.resize(1600, 900)

        self.project_controller: ProjectController | None = None
        self.ui_state = UIState()
        self.recent_projects = RecentProjects()

        build_menu(self)
        build_toolbar(self)
        build_statusbar(self)

        self.dashboard = Dashboard()
        self.workspace = Workspace()
        self.setCentralWidget(self.dashboard)

        self.dashboard.newProjectRequested.connect(self.new_project)
        self.dashboard.openProjectRequested.connect(self.open_project)

        self.projectDock = ProjectDock(self)
        self.outputDock = OutputDock(self)
        self.logDock = LogDock(self)

        self.addDockWidget(Qt.LeftDockWidgetArea, self.projectDock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.outputDock)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.logDock)

        self.restore_ui_state()
        self.refresh_recent_projects_menu()
        self.update_action_states()
        self.log("AI Content Studio started.")

    # --------------------------------------------------
    # Controller setup / events
    # --------------------------------------------------

    def set_project_controller(self, controller: ProjectController) -> None:
        if self.project_controller is controller:
            return

        self.project_controller = controller

        controller.projectOpened.connect(self._on_project_opened)
        controller.projectClosed.connect(self._on_project_closed)
        controller.projectSaved.connect(self._on_project_saved)
        controller.projectModified.connect(self._on_project_modified)
        controller.projectAutoSaved.connect(self._on_project_autosaved)
        controller.projectBackupCreated.connect(self._on_project_backup_created)
        controller.projectBackupRestored.connect(self._on_project_backup_restored)
        controller.projectRecoveryAvailable.connect(self._on_recovery_available)
        controller.projectRecovered.connect(self._on_project_recovered)

        self.update_project_title()
        self.update_action_states()

    def _on_project_opened(self, root) -> None:
        self.add_recent_project(str(root))
        self.projectDock.load_project(root)
        self.show_workspace()
        self.refresh_project_ui()
        self.statusBar().showMessage("Project opened.")
        self.log(f"Project opened: {root}")

    def _on_project_closed(self) -> None:
        self.projectDock.clear()
        self.show_dashboard()
        self.refresh_project_ui()
        self.statusBar().showMessage("Project closed.")
        self.log("Project closed.")

    def _on_project_saved(self, root) -> None:
        self.projectDock.refresh(root)
        self.refresh_project_ui()
        self.statusBar().showMessage("Project saved.")
        self.log(f"Project saved: {root}")

    def _on_project_modified(self, modified: bool) -> None:
        self.update_project_title()
        self.update_action_states()

    def _on_project_autosaved(self, recovery) -> None:
        self.statusBar().showMessage("Recovery snapshot saved.", 3000)
        self.log(f"Autosave recovery snapshot: {recovery}")

    def _on_project_backup_created(self, backup) -> None:
        self.statusBar().showMessage("Project backup created.", 3000)
        self.log(f"Project backup created: {backup}")

    def _on_project_backup_restored(self, root) -> None:
        self.projectDock.refresh(root)
        self.refresh_project_ui()
        self.statusBar().showMessage("Project backup restored.", 3000)
        self.log(f"Project backup restored: {root}")

    def _on_project_recovered(self, root) -> None:
        self.projectDock.refresh(root)
        self.refresh_project_ui()
        self.statusBar().showMessage("Recovery snapshot restored.", 3000)
        self.log(f"Project recovered: {root}")

    def _on_recovery_available(self, recovery) -> None:
        if self.project_controller is None:
            return

        choice = ProjectDialogs.confirm_recovery(self, recovery)

        try:
            if choice == "recover":
                if not self.project_controller.recover_project():
                    raise RuntimeError("Unable to recover project snapshot.")
                return

            if choice == "discard":
                self.project_controller.clear_recovery()
                self.log(f"Recovery snapshot discarded: {recovery}")
                return

            self.log(f"Recovery snapshot kept for later: {recovery}")

        except Exception as exc:
            self.show_error("Project Recovery Failed", exc)
            self.log(f"Recovery failed: {exc}")

    # --------------------------------------------------
    # Dashboard / workspace
    # --------------------------------------------------

    def show_workspace(self) -> None:
        if self.centralWidget() is not self.workspace:
            self.setCentralWidget(self.workspace)
        self.workspace.show()

    def show_dashboard(self) -> None:
        if self.centralWidget() is not self.dashboard:
            self.setCentralWidget(self.dashboard)
        self.dashboard.show()

    # --------------------------------------------------
    # Project operations
    # --------------------------------------------------

    def new_project(self) -> None:
        if self.project_controller is None:
            return

        if not self._prepare_for_project_switch():
            return

        result = ProjectDialogs.new_project(self)
        if not result:
            return

        name, path = result

        try:
            self.project_controller.create_project(path=path, name=name)
        except Exception as exc:
            self.show_error("Unable to create project", exc)
            self.log(f"Create project failed: {exc}")

    def open_project(self, path=None) -> None:
        if self.project_controller is None:
            return

        if isinstance(path, bool):
            path = None

        if path is None:
            path = ProjectDialogs.open_project(self)

        if not path:
            return

        if not self._prepare_for_project_switch():
            return

        try:
            self.project_controller.open_project(Path(path))
        except Exception as exc:
            self.show_error("Unable to open project", exc)
            self.log(f"Open project failed: {exc}")

    def save_project(self) -> bool:
        if self.project_controller is None or not self.project_controller.has_project():
            return False

        try:
            return self.project_controller.save_project()
        except Exception as exc:
            self.show_error("Unable to save project", exc)
            self.log(f"Save project failed: {exc}")
            return False

    def save_project_as(self) -> bool:
        if self.project_controller is None or not self.project_controller.has_project():
            return False

        path = ProjectDialogs.save_project_as(self)
        if not path:
            return False

        try:
            project = self.project_controller.save_project_as(path)
            return project is not None
        except Exception as exc:
            self.show_error("Unable to save project", exc)
            self.log(f"Save As failed: {exc}")
            return False

    def close_project(self) -> bool:
        if self.project_controller is None or not self.project_controller.has_project():
            return True

        if not self._confirm_unsaved_changes():
            return False

        try:
            return self.project_controller.close_project(force=True)
        except Exception as exc:
            self.show_error("Unable to close project", exc)
            self.log(f"Close project failed: {exc}")
            return False

    def refresh_project(self) -> bool:
        if self.project_controller is None or not self.project_controller.has_project():
            return False

        if self.project_controller.has_unsaved_changes():
            result = QMessageBox.question(
                self,
                "Reload Project",
                "Reloading will discard unsaved in-memory changes. Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if result != QMessageBox.Yes:
                return False

        try:
            project = self.project_controller.refresh()
            if project is None:
                return False
            self.projectDock.refresh(project.root)
            self.refresh_project_ui()
            self.statusBar().showMessage("Project refreshed.", 3000)
            return True
        except Exception as exc:
            self.show_error("Unable to refresh project", exc)
            self.log(f"Refresh project failed: {exc}")
            return False

    def _prepare_for_project_switch(self) -> bool:
        if self.project_controller is None or not self.project_controller.has_project():
            return True

        if not self._confirm_unsaved_changes():
            return False

        return self.project_controller.close_project(force=True)

    def _confirm_unsaved_changes(self) -> bool:
        if self.project_controller is None:
            return True

        if not self.project_controller.has_unsaved_changes():
            return True

        choice = ProjectDialogs.confirm_close(self)

        if choice == "cancel":
            return False

        if choice == "save":
            return self.save_project()

        return choice == "discard"

    # --------------------------------------------------
    # Backup management
    # --------------------------------------------------

    def create_project_backup(self) -> bool:
        if self.project_controller is None or not self.project_controller.has_project():
            return False

        try:
            backup = self.project_controller.create_backup()
            if backup is None:
                return False
            self.statusBar().showMessage(f"Backup created: {backup.name}", 4000)
            return True
        except Exception as exc:
            self.show_error("Unable to Create Backup", exc)
            self.log(f"Create backup failed: {exc}")
            return False

    def restore_project_backup(self) -> bool:
        if self.project_controller is None or not self.project_controller.has_project():
            return False

        backups = self.project_controller.list_backups()
        backup = ProjectDialogs.choose_backup(self, backups, "Restore Backup")
        if backup is None:
            return False

        if not ProjectDialogs.confirm_restore_backup(self, backup):
            return False

        try:
            return self.project_controller.restore_backup(backup)
        except Exception as exc:
            self.show_error("Unable to Restore Backup", exc)
            self.log(f"Restore backup failed: {exc}")
            return False

    def delete_project_backup(self) -> bool:
        if self.project_controller is None or not self.project_controller.has_project():
            return False

        backups = self.project_controller.list_backups()
        backup = ProjectDialogs.choose_backup(self, backups, "Delete Backup")
        if backup is None:
            return False

        if not ProjectDialogs.confirm_delete_backup(self, backup):
            return False

        try:
            deleted = self.project_controller.delete_backup(backup)
            if deleted:
                self.statusBar().showMessage(f"Backup deleted: {backup.name}", 3000)
                self.log(f"Backup deleted: {backup}")
            return deleted
        except Exception as exc:
            self.show_error("Unable to Delete Backup", exc)
            self.log(f"Delete backup failed: {exc}")
            return False

    def cleanup_project_backups(self) -> bool:
        if self.project_controller is None or not self.project_controller.has_project():
            return False

        backups = self.project_controller.list_backups()
        keep = ProjectDialogs.backup_cleanup_count(self, len(backups))
        if keep is None:
            return False

        try:
            removed = self.project_controller.cleanup_backups(keep=keep)
            self.statusBar().showMessage(f"Removed {removed} old backup(s).", 4000)
            self.log(f"Backup cleanup removed {removed} file(s); kept {keep}.")
            return True
        except Exception as exc:
            self.show_error("Unable to Cleanup Backups", exc)
            self.log(f"Backup cleanup failed: {exc}")
            return False

    # --------------------------------------------------
    # Recent projects
    # --------------------------------------------------

    def add_recent_project(self, path: str) -> None:
        if not path:
            return

        self.recent_projects.add(path)
        self.refresh_recent_projects_menu()

    def refresh_recent_projects_menu(self) -> None:
        if not hasattr(self, "recentProjectsMenu"):
            return

        self.recentProjectsMenu.clear()
        projects = self.recent_projects.get_all()

        for project in projects:
            action = QAction(project, self)
            action.triggered.connect(
                lambda checked=False, p=project: self.open_project(p)
            )
            self.recentProjectsMenu.addAction(action)

        if not projects:
            empty = QAction("No recent projects", self)
            empty.setEnabled(False)
            self.recentProjectsMenu.addAction(empty)

    # --------------------------------------------------
    # UI state
    # --------------------------------------------------

    def restore_ui_state(self) -> None:
        try:
            self.ui_state.restore_main_window(self)
        except Exception as exc:
            self.log(f"UI restore failed: {exc}")

    def save_ui_state(self) -> None:
        try:
            self.ui_state.save_main_window(self)
        except Exception as exc:
            self.log(f"UI state save failed: {exc}")

    # --------------------------------------------------
    # Window title / actions
    # --------------------------------------------------

    def update_project_title(self) -> None:
        title = "AI Content Studio"

        if self.project_controller is not None:
            project = self.project_controller.project
            if project is not None:
                title = f"{project.name} - AI Content Studio"
                if self.project_controller.modified:
                    title += " *"

        self.setWindowTitle(title)

    def update_action_states(self) -> None:
        has_project = self.has_project()

        for name in (
            "saveAction",
            "saveAsAction",
            "closeProjectAction",
            "exportAction",
            "toolbar_save",
            "toolbar_save_as",
            "toolbar_close",
            "refreshProjectAction",
            "createBackupAction",
            "restoreBackupAction",
            "deleteBackupAction",
            "cleanupBackupsAction",
        ):
            action = getattr(self, name, None)
            if action is not None:
                action.setEnabled(has_project)

        backup_menu = getattr(self, "backupMenu", None)
        if backup_menu is not None:
            backup_menu.setEnabled(has_project)

    # --------------------------------------------------
    # Logging / errors
    # --------------------------------------------------

    def log(self, message: str) -> None:
        try:
            if hasattr(self, "logDock"):
                self.logDock.append(message)
        except Exception:
            pass

    def show_error(self, title: str, error: Exception) -> None:
        QMessageBox.critical(self, title, str(error))

    # --------------------------------------------------
    # Application close
    # --------------------------------------------------

    def closeEvent(self, event) -> None:
        try:
            if not self._confirm_unsaved_changes():
                event.ignore()
                return

            if self.project_controller is not None and self.project_controller.has_project():
                self.project_controller.close_project(force=True)

            self.save_ui_state()
            event.accept()
        except Exception as exc:
            self.log(f"Close failed: {exc}")
            event.ignore()

    # --------------------------------------------------
    # Utility methods
    # --------------------------------------------------

    def current_project(self):
        if self.project_controller is None:
            return None
        return self.project_controller.project

    def has_project(self) -> bool:
        return (
            self.project_controller is not None
            and self.project_controller.has_project()
        )

    def refresh_project_ui(self) -> None:
        self.update_project_title()
        self.update_action_states()
        self.refresh_recent_projects_menu()
