from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
)

from desktop.ui.menu_bar import build_menu
from desktop.ui.tool_bar import build_toolbar
from desktop.ui.status_bar import build_statusbar

from desktop.ui.docks.project_dock import ProjectDock
from desktop.ui.docks.output_dock import OutputDock
from desktop.ui.docks.log_dock import LogDock


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AI Content Studio")

        self.resize(1600, 900)

        build_menu(self)
        build_toolbar(self)
        build_statusbar(self)

        self.setCentralWidget(
            QLabel(
                "<h1>Welcome to AI Content Studio</h1>"
            )
        )

        self.projectDock = ProjectDock(self)
        self.outputDock = OutputDock(self)
        self.logDock = LogDock(self)

        self.addDockWidget(
            Qt.LeftDockWidgetArea,
            self.projectDock
        )

        self.addDockWidget(
            Qt.RightDockWidgetArea,
            self.outputDock
        )

        self.addDockWidget(
            Qt.BottomDockWidgetArea,
            self.logDock
        )

        self.logDock.log("AI Content Studio started.")