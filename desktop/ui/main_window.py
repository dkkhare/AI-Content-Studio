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

    def new_project(
        self,
    ):

        try:

            path = ProjectDialogs.create_project(
                self
            )

            if not path:
                return


            controller = ProjectController.create(
                path
            )

            self.set_project_controller(
                controller
            )

            controller.open()


        except Exception as exc:

            self.show_error(
                "Unable to create project",
                exc,
            )

            self.log(
                f"Create project failed: {exc}"
            )


    def open_project(
        self,
        path=None,
    ):

        try:

            if not path:

                path = ProjectDialogs.open_project(
                    self
                )


            if not path:
                return


            controller = ProjectController.open(
                path
            )


            self.set_project_controller(
                controller
            )


            controller.open()


        except Exception as exc:

            self.show_error(
                "Unable to open project",
                exc,
            )

            self.log(
                f"Open project failed: {exc}"
            )


    def close_project(
        self,
    ):

        try:

            if self.project_controller:

                self.project_controller.close()

                self.project_controller = None


        except Exception as exc:

            self.show_error(
                "Unable to close project",
                exc,
            )

            self.log(
                f"Close project failed: {exc}"
            )


    def save_project(
        self,
    ):

        try:

            if not self.project_controller:

                return


            self.project_controller.save()


        except Exception as exc:

            self.show_error(
                "Unable to save project",
                exc,
            )

            self.log(
                f"Save project failed: {exc}"
            )


    def save_project_as(
        self,
    ):

        try:

            if not self.project_controller:

                return


            path = ProjectDialogs.save_as_project(
                self
            )


            if not path:
                return


            self.project_controller.save_as(
                path
            )


        except Exception as exc:

            self.show_error(
                "Unable to save project",
                exc,
            )

            self.log(
                f"Save As failed: {exc}"
            )