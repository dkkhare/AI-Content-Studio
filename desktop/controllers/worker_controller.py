from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject
from PySide6.QtCore import QThread


class WorkerController(QObject):
    """
    Generic controller for running a QObject worker
    inside its own QThread.
    """

    def __init__(
        self,
        worker,
        parent=None,
    ):

        super().__init__(parent)

        self.worker = worker

        self.thread: Optional[QThread] = None

    # --------------------------------------------------
    # Start Worker
    # --------------------------------------------------

    def start(self):

        if (
            self.thread is not None
            and self.thread.isRunning()
        ):
            return

        self.thread = QThread()

        self.worker.moveToThread(
            self.thread
        )

        self.thread.started.connect(
            self.worker.run
        )

        if hasattr(
            self.worker,
            "finished",
        ):
            self.worker.finished.connect(
                self.thread.quit
            )

        if hasattr(
            self.worker,
            "failed",
        ):
            self.worker.failed.connect(
                self.thread.quit
            )

        if hasattr(
            self.worker,
            "cancelled",
        ):
            self.worker.cancelled.connect(
                self.thread.quit
            )

        self.thread.finished.connect(
            self.cleanup
        )

        self.thread.start()

    # --------------------------------------------------
    # Stop Worker
    # --------------------------------------------------

    def stop(self):

        if hasattr(
            self.worker,
            "request_cancel",
        ):
            self.worker.request_cancel()

    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def cleanup(self):

        if self.thread is None:
            return

        self.thread.deleteLater()

        self.thread = None

    # --------------------------------------------------
    # Status
    # --------------------------------------------------

    def is_running(
        self,
    ) -> bool:

        return (
            self.thread is not None
            and
            self.thread.isRunning()
        )