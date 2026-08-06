from __future__ import annotations

from PySide6.QtCore import Qt
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

    Responsibilities
    ----------------
    • Display application welcome screen
    • Start new project workflow
    • Start open project workflow
    • Display workflow overview
    """

    newProjectRequested = Signal()

    openProjectRequested = Signal()

    recentProjectRequested = Signal(str)

    def __init__(
        self,
        parent=None,
    ):

        super().__init__(parent)

        self.workflow_panel = None

        self.new_project_button = None

        self.open_project_button = None

        self._busy = False

        self._build_ui()

        self._connect_signals()

    # --------------------------------------------------
    # UI Construction
    # --------------------------------------------------

    def _build_ui(
        self,
    ):

        main_layout = QHBoxLayout(self)

        main_layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )

        main_layout.setSpacing(20)

        left_layout = QVBoxLayout()

        left_layout.setSpacing(12)

        title = QLabel(
            "<h1>Welcome to AI Content Studio</h1>"
        )

        title.setAlignment(
            Qt.AlignLeft
        )

        subtitle = QLabel(
            "Create podcasts, audiobooks and AI videos completely offline."
        )

        subtitle.setWordWrap(True)

        self.new_project_button = QPushButton(
            "New Project"
        )

        self.open_project_button = QPushButton(
            "Open Project"
        )

        self.new_project_button.setMinimumHeight(42)

        self.open_project_button.setMinimumHeight(42)

        left_layout.addWidget(title)

        left_layout.addWidget(subtitle)

        left_layout.addSpacing(20)

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

        if self._busy:
            return

        self.newProjectRequested.emit()

    def _request_open_project(
        self,
    ):

        if self._busy:
            return

        self.openProjectRequested.emit()

    # --------------------------------------------------
    # Dashboard Refresh
    # --------------------------------------------------

    def refresh(
        self,
    ):
        """
        Refresh dashboard widgets.

        Called whenever application state changes.
        """

        if self.workflow_panel:

            try:

                self.workflow_panel.refresh()

            except Exception:

                pass

    # --------------------------------------------------
    # Busy State
    # --------------------------------------------------

    def set_busy(
        self,
        busy: bool,
    ):

        self._busy = busy

        self.set_enabled(
            not busy
        )

    def is_busy(
        self,
    ) -> bool:

        return self._busy

    # --------------------------------------------------
    # Enable / Disable Controls
    # --------------------------------------------------

    def set_enabled(
        self,
        enabled: bool,
    ):

        if self.new_project_button:

            self.new_project_button.setEnabled(
                enabled
            )

        if self.open_project_button:

            self.open_project_button.setEnabled(
                enabled
            )

    def enable_buttons(
        self,
    ):

        self.set_enabled(True)

    def disable_buttons(
        self,
    ):

        self.set_enabled(False)

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def workflow(
        self,
    ):

        return self.workflow_panel

    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def clear(
        self,
    ):
        """
        Reset dashboard state.
        """

        self._busy = False

        self.set_enabled(True)

        self.refresh()