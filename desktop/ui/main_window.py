afrom PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow

from desktop.project.project_controller import (
    ProjectController,
)

from desktop.project.project_dialogs import (
    ProjectDialogs,
)

from desktop.settings import (
    UIState,
    RecentProjects,
)

from desktop.ui.menu_bar import build_menu
from desktop.ui.tool_bar import build_toolbar
from desktop.ui.status_bar import build_statusbar

from desktop.ui.docks.project_dock import (
    ProjectDock,
)

from desktop.ui.docks.output_dock import (
    OutputDock,
)

from desktop.ui.docks.log_dock import (
    LogDock,
)

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
            900,
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
        # Initialize UI
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
        controller.projectModified.connect(

    self.on_project_modified

)

        controller.projectOpened.connect(

            lambda _:

            self._project_changed()

        )

        controller.projectClosed.connect(

            self._project_changed

        )

        controller.projectSaved.connect(

            lambda _:

            self.statusBar().showMessage(

                "Project saved"

            )

        )
      def on_project_modified(

          self,

          modified,

      b):

    self.update_project_title()
    # --------------------------------------------------
    # Project Operations
    # --------------------------------------------------

    def save_project(self):

        if self.project_controller is None:

            return

        self.project_controller.save_project()

        self.log(

            "Project saved."

        )

        self.update_action_states()

    def auto_save_project(self):

        if self.project_controller is None:

            return

        self.project_controller.auto_save()

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
         self.update_action_states()

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
         
        self.update_action_states()
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

        result = ProjectDialogs.new_project(
            self
        )

        if result is None:

            return

        name, directory = result

        project = self.project_controller.create_project(
            name,
            directory,
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

    def save_project_as(self):

        if self.project_controller is None:

            return

        directory = ProjectDialogs.save_project_as(
            self
        )

        if directory is None:

            return

        self.project_controller.save_project_as(
            directory
        )

        self.update_project_title()

        self.update_action_states()

        self.log(
            "Project saved as."
        )

    def close_project(self):

        if self.project_controller is None:

            return

        self.auto_save_project()

        self.project_controller.close_project()

        self.show_dashboard()

        self.update_project_title()

        self.update_action_states()

        self.log(
            "Project closed."
        )

    # --------------------------------------------------
    # Window Title
    # --------------------------------------------------

        def update_project_title(self):

    title = "AI Content Studio"

    if (

        self.project_controller

        and

        self.project_controller.has_project()

    ):

        title += (

            " - "

            + self.project_controller.project_name()

        )

        if self.project_controller.is_modified():

            title += " *"

    self.setWindowTitle(title)
    #0 --------------------------------------------------
    # Recent Projects
    # --------------------------------------------------

    def refresh_recent_projects_menu(self):

        if not hasattr(
            self,
            "recent_projects_menu",
        ):
            return

        self.recent_projects_menu.clear()

        projects = self.recent_projects_list()

        if not projects:

            action = QAction(

                "No Recent Projects",

                self,

            )

            action.setEnabled(False)

            self.recent_projects_menu.addAction(
                action
            )

            return

        for project in projects:

            action = QAction(

                project,

                self,

            )

            action.triggered.connect(

                lambda checked=False, p=project:

                self._open_recent_project(p)

            )

            self.recent_projects_menu.addAction(
                action
            )

    def _open_recent_project(

        self,

        project_path,

    ):

        if self.project_controller is None:

            return

        try:

            project = self.project_controller.open_project(

                project_path

            )

        except Exception as exc:

            self.log(

                str(exc)

            )

            return

        self.add_recent_project(

            str(project.root)

        )

        self.show_workspace()

        self.update_project_title()

        self.update_action_states()

        self.log(

            f"Opened recent project: {project.name}"

        )

    def add_recent_project(

        self,

        project_path,

    ):

        self.recent_projects.add(

            project_path

        )

        self.refresh_recent_projects_menu()

    def recent_projects_list(self):

        return self.recent_projects.projects()
    # --------------------------------------------------
    # Workspace Helpers
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

    # --------------------------------------------------
    # Action State
    # --------------------------------------------------

    def update_action_states(self):

        has_project = self.has_project()

        if hasattr(
            self,
            "action_save_project",
        ):

            self.action_save_project.setEnabled(
                has_project
            )

        if hasattr(
            self,
            "action_save_project_as",
        ):

            self.action_save_project_as.setEnabled(
                has_project
            )

        if hasattr(
            self,
            "action_close_project",
        ):

            self.action_close_project.setEnabled(
                has_project
            )

        if hasattr(
            self,
            "toolbar_save",
        ):

            self.toolbar_save.setEnabled(
                has_project
            )
    # --------------------------------------------------
    # Close Event
    # --------------------------------------------------

    def closeEvent(

        self,

        event,

    ):

        try:

            self.auto_save_project()

        except Exception as exc:

            self.log(

                f"Auto-save failed: {exc}"

            )

        try:

            self.save_ui_state()

        except Exception as exc:

            self.log(

                f"Failed to save UI state: {exc}"

            )

        super().closeEvent(

            event

        )
# --------------------------------------------------
# Controller Signals
# --------------------------------------------------

def on_project_opened(
    self,
    project,
):

    self.update_project_title()

    self.update_action_states()

    self.refresh_recent_projects_menu()

    self.statusBar().showMessage(

        f"Opened: {project.name}"

    )

def on_project_saved(self):

    self.statusBar().showMessage(

        "Project saved"

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
    def _project_changed(self):

        self.update_project_title()

        self.update_action_states()

        self.refresh_recent_projects_menu()
    # --------------------------------------------------
    # Current Project
    # --------------------------------------------------

    def current_project_directory(self):

        if self.project_controller is None:

            return None

        return self.project_controller.project_directory()