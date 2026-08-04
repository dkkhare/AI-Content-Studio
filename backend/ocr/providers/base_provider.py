from abc import ABC, abstractmethod


class OCRProvider(ABC):

    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def recognize(self, image_path):
        pass