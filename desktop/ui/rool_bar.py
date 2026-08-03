from PySide6.QtCore import Qt
from PySide6.QtGui import QAction


def build_toolbar(window):

    toolbar = window.addToolBar("Main")

    toolbar.setMovable(False)

    toolbar.setToolButtonStyle(
        Qt.ToolButtonTextUnderIcon
    )

    toolbar.addAction(QAction("Import PDF", window))

    toolbar.addAction(QAction("Import Voice", window))

    toolbar.addAction(QAction("Import Image", window))

    toolbar.addSeparator()

    toolbar.addAction(QAction("Generate", window))