from PySide6.QtCore import (
    QObject,
    Signal,
)


class PDFWorker(QObject):

    progress = Signal(object)

    finished = Signal()

    error = Signal(str)

    def __init__(

        self,

        backend_worker,

        pdf,

    ):

        super().__init__()

        self.backend = backend_worker

        self.pdf = pdf

    def run(self):

        try:

            self.backend.process(

                self.pdf,

                self.progress.emit,

            )

            self.finished.emit()

        except Exception as e:

            self.error.emit(str(e))