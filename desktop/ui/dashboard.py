from __future__ import annotations

from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
)

from desktop.ui.workflow_panel import WorkflowPanel


class Dashboard(QWidget):
    """
    Landing page displayed when the application starts.

    Responsibilities:
    - Display application welcome screen
    - Start new project workflow
    - Start open project workflow

    Project operations are handled by MainWindow /
    ProjectController.
    """

    newProjectRequested = Signal()

    openProjectRequested = Signal()


    def __init__(
        self,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.workflow_panel = None

        self.new_project_button = None

        self.open_project_button = None


        self._build_ui()

        self._connect_signals()


    # --------------------------------------------------
    # UI Construction
    # --------------------------------------------------

    def _build_ui(
        self,
    ):

        main_layout = QHBoxLayout(
            self
        )


        left_layout = QVBoxLayout()


        title = QLabel(
            "<h1>Welcome to AI Content Studio</h1>"
        )


        subtitle = QLabel(
            "Create podcasts, audiobooks and AI videos completely offline."
        )


        self.new_project_button = QPushButton(
            "New Project"
        )


        self.open_project_button = QPushButton(
            "Open Project"
        )


        left_layout.addWidget(
            title
        )


        left_layout.addWidget(
            subtitle
        )


        left_layout.addSpacing(
            20
        )


        left_layout.addWidget(
            self.new_project_button
        )


        left_layout.addWidget(
            self.open_project_button
        )


        left_layout.addStretch()


        self.workflow_panel = WorkflowPanel()


        main_layout.addLayout(
            left_layout,
            2,
        )


        main_layout.addWidget(
            self.workflow_panel,
            1,
        )
    # --------------------------------------------------
    # Signal Connections
    # --------------------------------------------------

    def _connect_signals(
        self,
    ):

        self.new_project_button.clicked.connect(
            self._request_new_project
        )


        self.open_project_button.clicked.connect(
            self._request_open_project
        )


    # --------------------------------------------------
    # User Actions
    # --------------------------------------------------

    def _request_new_project(
        self,
    ):

        self.newProjectRequested.emit()


    def _request_open_project(
        self,
    ):

        self.openProjectRequested.emit()


    # --------------------------------------------------
    # Dashboard Refresh
    # --------------------------------------------------

    def refresh(
        self,
    ):

        """
        Refresh dashboard widgets.

        Called when returning from workspace
        or when application state changes.
        """

        if self.workflow_panel:

            self.workflow_panel.refresh()


    # --------------------------------------------------
    # Enable / Disable Controls
    # --------------------------------------------------

    def set_enabled(
        self,
        enabled: bool,
    ):

        self.new_project_button.setEnabled(
            enabled
        )

        self.open_project_button.setEnabled(
            enabled
        )


    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def clear(
        self,
    ):

        """
        Reset dashboard state.
        """

        self.refresh()