from abc import ABC
from abc import abstractmethod


class PDFSignals(ABC):

    @abstractmethod
    def on_started(self):
        pass

    @abstractmethod
    def on_progress(self, progress):
        pass

    @abstractmethod
    def on_finished(self):
        pass

    @abstractmethod
    def on_error(self, message):
        pass