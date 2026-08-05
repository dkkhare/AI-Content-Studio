from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow

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

        build_menu(self)

        build_toolbar(self)

        build_statusbar(self)

        # ------------------------------------------
        # Central Widgets
        # ------------------------------------------

        self.dashboard = Dashboard()

        self.workspace = Workspace()

        self.setCentralWidget(
            self.dashboard
        )

        # ------------------------------------------
        # Connect Dashboard
        # ------------------------------------------

        self.dashboard.newProjectRequested.connect(
            self.show_workspace
        )

        self.dashboard.openProjectRequested.connect(
            self.show_workspace
        )

        # ------------------------------------------
        # Docks
        # ------------------------------------------

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
    # Logging
    # --------------------------------------------------

    def log(

        self,

        message,

    ):

        self.logDock.log(message)

    # --------------------------------------------------
    # Workspace
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

        self.log(

            "Workspace opened."

        )

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def narration_panel(self):

        return self.workspace.narration()

    def open_pdf_workspace(self):

        self.show_workspace()

        self.workspace.open_pdf_tab()

    def open_ocr_workspace(self):

        self.show_workspace()

        self.workspace.open_ocr_tab()

    def open_narration_workspace(self):

        self.show_workspace()

        self.workspace.open_narration_tab()

    def open_translation_workspace(self):

        self.show_workspace()

        self.workspace.open_translation_tab()

    def open_video_workspace(self):

        self.show_workspace()

        self.workspace.open_video_tab()

    def open_export_workspace(self):

        self.show_workspace()

        self.workspace.open_export_tab()