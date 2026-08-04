from backend.pdf.worker import PDFWorker as BackendWorker

from desktop.ui.workers.pdf_worker import PDFWorker

from desktop.controllers.worker_controller import (

    WorkerController

)


class ImportController:

    def import_pdf(

        self,

        pdf,

    ):

        worker = PDFWorker(

            BackendWorker(),

            pdf,

        )

        WorkerController(

            worker

        )