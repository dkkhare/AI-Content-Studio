from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
)

from desktop.ui.workflow_panel import WorkflowPanel


class Dashboard(QWidget):

    def __init__(self):

        super().__init__()

        main = QHBoxLayout(self)

        left = QVBoxLayout()

        title = QLabel(
            "<h1>Welcome to AI Content Studio</h1>"
        )

        subtitle = QLabel(
            "Create podcasts, audiobooks and AI videos completely offline."
        )

        new_project = QPushButton("New Project")

        open_project = QPushButton("Open Project")

        left.addWidget(title)

        left.addWidget(subtitle)

        left.addSpacing(20)

        left.addWidget(new_project)

        left.addWidget(open_project)

        left.addStretch()

        workflow = WorkflowPanel()

        main.addLayout(left, 2)

        main.addWidget(workflow, 1)