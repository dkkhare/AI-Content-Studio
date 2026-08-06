from __future__ import annotations

from PySide6.QtCore import (
    QObject,
    Signal,
)


class PDFWorker(QObject):
    """
    Qt wrapper around the backend PDF processor.

    Runs inside a QThread and forwards
    backend progress/events to the UI.
    """

    started = Signal()

    progress = Signal(object)

    finished = Signal()

    error = Signal(str)

    cancelled = Signal()


    def __init__(
        self,
        backend_worker,
        pdf,
        parent=None,
    ):

        super().__init__(parent)

        self.backend = backend_worker

        self.pdf = pdf

        self._cancel_requested = False


    # --------------------------------------------------
    # Control
    # --------------------------------------------------

    def cancel(self):

        self._cancel_requested = True

        if hasattr(
            self.backend,
            "cancel",
        ):
            self.backend.cancel()


    # --------------------------------------------------
    # Worker Entry
    # --------------------------------------------------

    def run(self):

        self.started.emit()

        try:

            if self._cancel_requested:

                self.cancelled.emit()

                return


            self.backend.process(

                self.pdf,

                self.progress.emit,

            )


            if self._cancel_requested:

                self.cancelled.emit()

                return


            self.finished.emit()


        except Exception as exc:

            self.error.emit(
                str(exc)
            )