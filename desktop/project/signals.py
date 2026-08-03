from PySide6.QtCore import QObject
from PySide6.QtCore import Signal


class ProjectSignals(QObject):

    projectOpened = Signal(str)

    projectSaved = Signal(str)

    projectClosed = Signal()