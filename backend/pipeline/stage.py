from abc import ABC, abstractmethod


class PipelineStage(ABC):
    """
    Base class for every processing stage.
    """

    name = "Unnamed Stage"

    @abstractmethod
    def execute(self, context):
        """Run the stage."""
        raise NotImplementedError