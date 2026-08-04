from abc import ABC
from abc import abstractmethod


class NarrationCallback(ABC):

    @abstractmethod
    def on_started(self, job):
        pass

    @abstractmethod
    def on_progress(
        self,
        current,
        total,
    ):
        pass

    @abstractmethod
    def on_finished(
        self,
        output_file,
    ):
        pass

    @abstractmethod
    def on_error(
        self,
        message,
    ):
        pass