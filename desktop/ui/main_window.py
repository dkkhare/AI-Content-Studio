from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow

from desktop.project.project_controller import (
    ProjectController,
)

from desktop.settings import (
    UIState,
    RecentProjects,
)

from desktop.ui.menu_bar import build_menu
from desktop.ui.tool_bar import build_toolbar
from desktop.ui.status_bar import build_statusbar

from desktop.ui.docks.project_dock import ProjectDock
from desktop.ui.docks.output_dock import OutputDock
from desktop.ui.docks.log_dock import LogDock

from desktop.ui.dashboard import Dashboard
from desktop.ui.workspace import Workspace


class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("AI Content Studio")

        self.resize(1600, 900)

        # --------------------------------------------------
        # Project Controller
        # --------------------------------------------------

        self.project_controller = None

        build_menu(self)

        build_toolbar(self)

        build_statusbar(self)

        # --------------------------------------------------
        # Settings
        # --------------------------------------------------

        self.ui_state = UIState()

        self.recent_projects = RecentProjects()

        # --------------------------------------------------
        # Central Widgets
        # --------------------------------------------------

        self.dashboard = Dashboard()

        self.workspace = Workspace()

        self.setCentralWidget(
            self.dashboard
        )

        # --------------------------------------------------
        # Dashboard Connections
        # --------------------------------------------------

        self.dashboard.newProjectRequested.connect(
            self.show_workspace
        )

        self.dashboard.openProjectRequested.connect(
            self.show_workspace
        )

        # --------------------------------------------------
        # Docks
        # --------------------------------------------------

        self.projectDock = ProjectDock(self)

        self.outputDock = OutputDock(self)

        self.logDock = LogDock(self)

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

        self.log(
            "AI Content Studio started."
        )

    # --------------------------------------------------
    # Project Controller
    # --------------------------------------------------

    def set_project_controller(
        self,
        controller: ProjectController,
    ):

        self.project_controller = controller

    def project(self):

        if self.project_controller:

            return self.project_controller.current

        return None

    def has_project(self):

        return (
            self.project_controller is not None
            and
            self.project_controller.has_project()
        )

    def save_project(self):

        if self.project_controller:

            self.project_controller.save_project()

    def auto_save_project(self):

        if self.project_controller:

            self.project_controller.auto_save()

    # --------------------------------------------------
    # Logging
    # --------------------------------------------------

    def log(
        self,
        message,
    ):

        self.logDock.log(message)

    # --------------------------------------------------
    # Dashboard / Workspace
    # --------------------------------------------------

    def show_dashboard(self):

        self.setCentralWidget(
            self.dashboard
        )

        self.statusBar().showMessage(
            "Dashboard"
        )

        self.log(
            "Dashboard opened."
        )

    def show_workspace(self):

        self.setCentralWidget(
            self.workspace
        )

        self.statusBar().showMessage(
            "Workspace"
        )

        self.ui_state.restore_workspace(
            self.workspace
        )

        self.log(
            "Workspace opened."
        )

    # --------------------------------------------------
    # UI State
    # --------------------------------------------------

    def save_ui_state(self):

        self.ui_state.save_workspace(
            self.workspace
        )

        self.ui_state.save_narration(
            self.narration_panel()
        )

        self.ui_state.save_main_window(
            self
        )

    def restore_ui_state(self):

        self.ui_state.restore_main_window(
            self
        )

        self.ui_state.restore_workspace(
            self.workspace
        )

        self.ui_state.restore_narration