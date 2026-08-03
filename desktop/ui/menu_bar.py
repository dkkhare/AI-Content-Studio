from PySide6.QtGui import QAction


def build_menu(window):

    menu = window.menuBar()

    file_menu = menu.addMenu("&File")

    project_menu = menu.addMenu("&Project")

    ai_menu = menu.addMenu("&AI")

    tools_menu = menu.addMenu("&Tools")

    help_menu = menu.addMenu("&Help")

    file_menu.addAction(QAction("New Project", window))

    file_menu.addAction(QAction("Open Project", window))

    file_menu.addSeparator()

    file_menu.addAction(QAction("Exit", window))