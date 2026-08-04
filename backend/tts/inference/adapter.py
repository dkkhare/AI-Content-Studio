from abc import ABC, abstractmethod


class InferenceAdapter(ABC):
    """
    Common interface for all TTS inference backends.
    """

    @abstractmethod
    def load(self):
        pass

    @abstractmethod
    def synthesize(
        self,
        reference_audio,
        text,
        output_file,
    ):
        pass