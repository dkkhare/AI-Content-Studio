from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow

from desktop.controllers.project_controller import ProjectController
from desktop.project.project_dialog import ProjectDialogs

from desktop.settings import (
    UIState,
    RecentProjects,
    SettingsManager,
)

from desktop.ui.menu_bar import build_menu
from desktop.ui.tool_bar import build_toolbar
from desktop.ui.status_bar import build_statusbar

from desktop.ui.docks.project_dock import ProjectDock
from desktop.ui.docks.output_dock import OutputDock
from desktop.ui.docks.log_dock import LogDock
from desktop.ui.docks.ai_assistant_dock import AIAssistantDock

from desktop.ui.dashboard import Dashboard
from desktop.ui.workspace import Workspace
from desktop.ai import AISettingsStore
from desktop.controllers.ai_controller import AIDesktopController
from desktop.ui.dialogs.ai_settings_dialog import AISettingsDialog


class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "AI Content Studio"
        )

        self.resize(
            1600,
            900
        )

        # --------------------------------------------------
        # Project Controller
        # --------------------------------------------------

        self.project_controller = None

        # --------------------------------------------------
        # Menu / Toolbar / Status Bar
        # --------------------------------------------------

        build_menu(self)

        build_toolbar(self)

        build_statusbar(self)

        # --------------------------------------------------
        # Settings
        # --------------------------------------------------

        self.ui_state = UIState()

        self.recent_projects = RecentProjects()

        self.ai_settings_store = AISettingsStore(SettingsManager())
        self.ai_controller = AIDesktopController()
        self.ai_controller.configure(self.ai_settings_store.load())

        # --------------------------------------------------
        # Central Widgets
        # --------------------------------------------------

        self.dashboard = Dashboard()

        self.workspace = Workspace()

        self.setCentralWidget(
            self.dashboard
        )

        # --------------------------------------------------
        # Dashboard Signals
        # --------------------------------------------------

        self.dashboard.newProjectRequested.connect(
            self.new_project
        )

        self.dashboard.openProjectRequested.connect(
            self.open_project
        )

        # --------------------------------------------------
        # Docks
        # --------------------------------------------------

        self.projectDock = ProjectDock(
            self
        )

        self.outputDock = OutputDock(
            self
        )

        self.logDock = LogDock(
            self
        )

        self.aiAssistantDock = AIAssistantDock(
            self.ai_controller,
            self,
        )

        self.addDockWidget(
            Qt.LeftDockWidgetArea,
            self.projectDock,
        )

        self.addDockWidget(
            Qt.RightDockWidgetArea,
            self.outputDock,
        )

        self.addDockWidget(
            Qt.BottomDockWidgetArea,
            self.logDock,
        )

        self.addDockWidget(
            Qt.RightDockWidgetArea,
            self.aiAssistantDock,
        )
        self.aiAssistantDock.hide()

        # --------------------------------------------------
        # Initial State
        # --------------------------------------------------

        self.restore_ui_state()

        self.refresh_recent_projects_menu()

        self.update_action_states()

        self.log(
            "AI Content Studio started."
        )


    # --------------------------------------------------
    # Project Controller Setup
    # --------------------------------------------------

    def set_project_controller(
        self,
        controller: ProjectController,
    ):

        self.project_controller = controller

        controller.projectOpened.connect(
            self._on_project_opened
        )

        controller.projectClosed.connect(
            self._on_project_closed
        )

        controller.projectSaved.connect(
            self._on_project_saved
        )

        controller.projectModified.connect(
            self._on_project_modified
        )


    # --------------------------------------------------
    # Controller Events
    # --------------------------------------------------

    def _on_project_opened(
        self,
        root,
    ):

        self.add_recent_project(
            str(root)
        )

        self.show_workspace()
        self.aiAssistantDock.set_project(self.current_project())

        self.update_project_title()

        self.update_action_states()

        self.statusBar().showMessage(
            "Project opened."
        )

        self.log(
            "Project opened."
        )


    def _on_project_closed(
        self,
    ):

        self.show_dashboard()
        self.aiAssistantDock.set_project(None)

        self.update_project_title()

        self.update_action_states()

        self.statusBar().showMessage(
            "Project closed."
        )

        self.log(
            "Project closed."
        )
    # --------------------------------------------------
    # Project Events
    # --------------------------------------------------

    def _on_project_saved(
        self,
    ):

        self.update_project_title()

        self.update_action_states()

        self.statusBar().showMessage(
            "Project saved."
        )

        self.log(
            "Project saved successfully."
        )


    def _on_project_modified(
        self,
    ):

        self.update_project_title()

        self.update_action_states()


    # --------------------------------------------------
    # Dashboard / Workspace Switching
    # --------------------------------------------------

    def show_workspace(
        self,
    ):

        if self.centralWidget() != self.workspace:

            self.setCentralWidget(
                self.workspace
            )

        self.workspace.show()


    def show_dashboard(
        self,
    ):

        if self.centralWidget() != self.dashboard:

            self.setCentralWidget(
                self.dashboard
            )

        self.dashboard.show()


    # --------------------------------------------------
    # Project Operations
    # --------------------------------------------------

    def new_project(self):
        try:
            result = ProjectDialogs.new_project(self)
            if not result:
                return
            name, path = result
            if self.project_controller is None:
                self.set_project_controller(ProjectController(self))
            self.project_controller.create_project(path, name)
        except Exception as exc:
            self.show_error("Unable to create project", exc)
            self.log(f"Create project failed: {exc}")

    def open_project(self, path=None):
        try:
            path = path or ProjectDialogs.open_project(self)
            if not path:
                return
            if self.project_controller is None:
                self.set_project_controller(ProjectController(self))
            self.project_controller.open_project(path)
        except Exception as exc:
            self.show_error("Unable to open project", exc)
            self.log(f"Open project failed: {exc}")

    def close_project(self):
        try:
            if self.project_controller:
                self.project_controller.close_project()
        except Exception as exc:
            self.show_error("Unable to close project", exc)
            self.log(f"Close project failed: {exc}")

    def save_project(self):
        try:
            if self.project_controller:
                self.project_controller.save_project()
        except Exception as exc:
            self.show_error("Unable to save project", exc)
            self.log(f"Save project failed: {exc}")

    def save_project_as(self):
        try:
            if not self.project_controller:
                return
            path = ProjectDialogs.save_project_as(self)
            if path:
                self.project_controller.save_project_as(path)
        except Exception as exc:
            self.show_error("Unable to save project", exc)
            self.log(f"Save As failed: {exc}")

    def add_recent_project(
        self,
        path: str,
    ):

        if not path:
            return

        self.recent_projects.add(
            path
        )

        self.refresh_recent_projects_menu()


    def refresh_recent_projects_menu(
        self,
    ):

        try:

            if hasattr(
                self,
                "recentProjectsMenu"
            ):

                self.recentProjectsMenu.clear()

                projects = (
                    self.recent_projects.get_all()
                )

                for project in projects:

                    action = QAction(
                        project,
                        self,
                    )

                    action.triggered.connect(
                        lambda checked=False,
                        p=project:
                        self.open_project(p)
                    )

                    self.recentProjectsMenu.addAction(
                        action
                    )


        except Exception as exc:

            self.log(
                f"Recent projects refresh failed: {exc}"
            )


    # --------------------------------------------------
    # UI State Management
    # --------------------------------------------------

    def restore_ui_state(
        self,
    ):

        try:

            geometry = (
                self.ui_state.window_geometry()
            )

            if geometry:

                self.restoreGeometry(
                    geometry
                )


            state = (
                self.ui_state.window_state()
            )

            if state:

                self.restoreState(
                    state
                )


        except Exception as exc:

            self.log(
                f"UI restore failed: {exc}"
            )


    def save_ui_state(
        self,
    ):

        try:

            self.ui_state.set_window_geometry(
                self.saveGeometry()
            )

            self.ui_state.set_window_state(
                self.saveState()
            )


            self.ui_state.save()


        except Exception as exc:

            self.log(
                f"UI state save failed: {exc}"
            )


    # --------------------------------------------------
    # Window Title
    # --------------------------------------------------

    def update_project_title(
        self,
    ):

        title = (
            "AI Content Studio"
        )


        if self.project_controller:

            project = self.project_controller.current_project()


            if project:

                name = getattr(
                    project,
                    "name",
                    None,
                )


                if name:

                    title = (
                        f"{name} - "
                        "AI Content Studio"
                    )


                if getattr(
                    project,
                    "is_modified",
                    False,
                ):

                    title += " *"


        self.setWindowTitle(
            title
        )


    # --------------------------------------------------
    # Action State Management
    # --------------------------------------------------

    def update_action_states(
        self,
    ):

        has_project = (
            self.project_controller
            is not None
        )


        if hasattr(
            self,
            "saveAction",
        ):

            self.saveAction.setEnabled(
                has_project
            )


        if hasattr(
            self,
            "saveAsAction",
        ):

            self.saveAsAction.setEnabled(
                has_project
            )


        if hasattr(
            self,
            "closeProjectAction",
        ):

            self.closeProjectAction.setEnabled(
                has_project
            )


        if hasattr(
            self,
            "exportAction",
        ):

            self.exportAction.setEnabled(
                has_project
            )
    # --------------------------------------------------
    # Logging
    # --------------------------------------------------

    def log(
        self,
        message: str,
    ):

        try:

            if hasattr(
                self,
                "logDock",
            ):

                self.logDock.append(
                    message
                )


        except Exception:

            pass


    # --------------------------------------------------
    # Error Handling
    # --------------------------------------------------

    def show_error(
        self,
        title: str,
        error: Exception,
    ):

        from PySide6.QtWidgets import QMessageBox


        QMessageBox.critical(
            self,
            title,
            str(error),
        )


    # --------------------------------------------------
    # AI Provider Settings
    # --------------------------------------------------

    def open_ai_settings(self):
        dialog = AISettingsDialog(
            self.ai_controller,
            self.ai_settings_store,
            self,
        )
        if dialog.exec():
            self.aiAssistantDock.refresh_profile()
            self.statusBar().showMessage("AI provider settings updated.")
            self.log("AI provider settings updated.")

    def show_ai_workbench(self):
        self.aiAssistantDock.show()
        self.aiAssistantDock.raise_()
        self.aiAssistantDock.refresh_profile()

    # --------------------------------------------------
    # Application Close
    # --------------------------------------------------

    def closeEvent(
        self,
        event,
    ):

        try:

            if self.project_controller:

                if (
                    hasattr(
                        self.project_controller,
                        "has_unsaved_changes",
                    )
                    and
                    self.project_controller.has_unsaved_changes()
                ):

                    result = ProjectDialogs.confirm_close(
                        self
                    )

                    if not result:

                        event.ignore()

                        return


                self.project_controller.close_project(force=True)

            if self.workspace:
                self.workspace.dispose()

            self.save_ui_state()


            event.accept()


        except Exception as exc:

            self.log(
                f"Close failed: {exc}"
            )

            event.accept()


    # --------------------------------------------------
    # Utility Methods
    # --------------------------------------------------

    def current_project(
        self,
    ):

        if self.project_controller:
            return self.project_controller.current_project()

        return None


    def has_project(
        self,
    ) -> bool:

        return (
            self.project_controller
            is not None
        )


    def refresh_project_ui(
        self,
    ):

        """
        Central UI refresh method.

        Milestone 10.5 improvement:
        Avoid repeated calls to:
        - update_project_title()
        - update_action_states()
        - refresh_recent_projects_menu()
        """

        self.update_project_title()

        self.update_action_states()

        self.refresh_recent_projects_menu()


    # --------------------------------------------------
    # End of MainWindow
    # --------------------------------------------------