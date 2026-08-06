from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow

from desktop.project.project_controller import ProjectController
from desktop.project.project_dialogs import ProjectDialogs

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

        # --------------------------------------------------
        # Central Widgets
        # --------------------------------------------------

        self.dashboard = Dashboard()
        self.workspace = Workspace()

        self.setCentralWidget(self.dashboard)

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

        # --------------------------------------------------
        # Initialize
        # --------------------------------------------------

        self.refresh_recent_projects_menu()
        self.update_action_states()

        self.log(
            "AI Content Studio started."
        )