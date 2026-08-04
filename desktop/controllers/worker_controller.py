from PySide6.QtCore import QThread


class WorkerController:

    def __init__(

        self,

        worker,

    ):

        self.thread = QThread()

        worker.moveToThread(

            self.thread

        )

        self.thread.started.connect(

            worker.run

        )

        worker.finished.connect(

            self.thread.quit

        )

        self.thread.start()