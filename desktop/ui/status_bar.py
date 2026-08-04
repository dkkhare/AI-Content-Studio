from PySide6.QtWidgets import QLabel


def build_statusbar(window):

    status = window.statusBar()

    status.addPermanentWidget(
        QLabel("Ready")
    )