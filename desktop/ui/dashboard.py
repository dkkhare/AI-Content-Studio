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
    """

    newProjectRequested = Signal()

    openProjectRequested = Signal()

    def __init__(self):

        super().__init__()

        self._build_ui()

        self._connect_signals()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def _build_ui(self):

        main = QHBoxLayout(self)

        left = QVBoxLayout()

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

        left.addWidget(title)

        left.addWidget(subtitle)

        left.addSpacing(20)

        left.addWidget(
            self.new_project_button
        )

        left.addWidget(
            self.open_project_button
        )

        left.addStretch()

        workflow = WorkflowPanel()

        main.addLayout(left, 2)

        main.addWidget(workflow, 1)

    # --------------------------------------------------
    # Connections
    # --------------------------------------------------

    def _connect_signals(self):

        self.new_project_button.clicked.connect(
            self._new_project_clicked
        )

        self.open_project_button.clicked.connect(
            self._open_project_clicked
        )

    # --------------------------------------------------
    # Button Handlers
    # --------------------------------------------------

    def _new_project_clicked(self):

        self.newProjectRequested.emit()

    def _open_project_clicked(self):

        self.openProjectRequested.emit()

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def enable_buttons(self):

        self.new_project_button.setEnabled(True)

        self.open_project_button.setEnabled(True)

    def disable_buttons(self):

        self.new_project_button.setEnabled(False)

        self.open_project_button.setEnabled(False)