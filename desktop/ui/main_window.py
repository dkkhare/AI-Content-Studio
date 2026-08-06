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

    # --------------------------------------------------
    # Project Controller
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
    # Controller Slots
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

    def _on_project_closed(self):

        self.show_dashboard()

        self.update_project_title()

        self.update_action_states()

        self.statusBar().showMessage(
            "Project closed."
        )

        self.log(
            "Project closed."
        )
    def _on_project_saved(

        self,

        path,

    ):

        self.update_project_title()

        self.statusBar().showMessage(

            "Project saved."

        )

        self.log(

            "Project saved."

        )

    def _on_project_modified(

        self,

        modified,

    ):

        self.update_project_title()

    # --------------------------------------------------
    # Logging
    # --------------------------------------------------

    def log(

        self,

        message,

    ):

        self.logDock.log(

            message

        )

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

        self.update_project_title()

        self.update_action_states()

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

        self.update_project_title()

        self.update_action_states()

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

        self.ui_state.restore_narration(

            self.narration_panel()

        )

    # --------------------------------------------------
    # Project Actions
    # --------------------------------------------------

    def new_project(self):

        if self.project_controller is None:

            return

        )

        self.add_recent_project(

            str(project.root)

        )

        self.show_workspace()

        self.update_project_title()

        self.update_action_states()

        self.log(

            f"Project created: {project.name}"

        )

    def open_project(self):

        if self.project_controller is None:

            return

        directory = ProjectDialogs.open_project(

            self

        )

        if directory is None:

            return

        project = self.project_controller.open_project(

            directory

        )

        self.add_recent_project(

            str(project.root)

        )

        self.show_workspace()

        self.update_project_title()

        self.update_action_states()

        self.log(

            f"Project opened: {project.name}"

        )

    def save_project(self):

        if self.project_controller is None:

            return

        if self.project_controller.save_project():

            self.statusBar().showMessage(

                "Project saved."

            )

            self.update_project_title()

            self.update_action_states()

    def save_project_as(self):

        if self.project_controller is None:

            return

        directory = ProjectDialogs.save_project_as(

            self

        )

        if directory is None:

            return

        if self.project_controller.save_project_as(

            directory

        ):

            self.add_recent_project(

                str(directory)

            )

            self.update_project_title()

            self.update_action_states()

            self.statusBar().showMessage(

                "Project saved."

            )

            self.log(

                "Project saved as."

            )

    def close_project(self):

        if self.project_controller is None:

            return

        if self.project_controller.has_project():

            self.auto_save_project()

            self.project_controller.close_project()

        self.show_dashboard()

        self.update_project_title()

        self.update_action_states()

        self.log(

            "Project closed."

        )

    def auto_save_project(self):

        if self.project_controller is None:

            return

        self.project_controller.auto_save()