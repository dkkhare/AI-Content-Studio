from __future__ import annotations

from backend.pdf.worker import PDFWorker as BackendWorker

from desktop.ui.workers.pdf_worker import PDFWorker

from desktop.controllers.worker_controller import (
    WorkerController,
)


class ImportController:
    """
    Controller responsible for importing PDF files
    through the background worker framework.
    """

    def __init__(self):

        self.worker = None

        self.controller = None

    # --------------------------------------------------
    # Import PDF
    # --------------------------------------------------

    def import_pdf(
        self,
        pdf,
    ):

        self.worker = PDFWorker(
            BackendWorker(),
            pdf,
        )

        self.controller = WorkerController(
            self.worker
        )

        self.controller.start()

        return self.worker

    # --------------------------------------------------
    # Status
    # --------------------------------------------------

    def is_running(self):

        if self.controller is None:
            return False

        return self.controller.is_running()

    # --------------------------------------------------
    # Cancel
    # --------------------------------------------------

    def cancel(self):

        if self.controller:

            self.controller.stop()

    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def reset(self):

        self.worker = None

        self.controller = None