from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable


class PipelineStage(ABC):
    """Base class for every processing stage."""

    stage_id = "stage"
    name = "Unnamed Stage"
    weight = 1.0

    def __init__(self, stage_id: str | None = None, name: str | None = None, weight: float | None = None):
        if stage_id:
            self.stage_id = str(stage_id)
        if name:
            self.name = str(name)
        if weight is not None:
            self.weight = max(0.0001, float(weight))

    @abstractmethod
    def execute(self, context, progress: Callable[[int, str], None] | None = None):
        """Run the stage and optionally report 0-100 stage progress."""
        raise NotImplementedError


class FunctionStage(PipelineStage):
    """Small adapter that turns a callable into a pipeline stage."""

    def __init__(self, stage_id: str, name: str, function, weight: float = 1.0):
        super().__init__(stage_id=stage_id, name=name, weight=weight)
        self.function = function

    def execute(self, context, progress=None):
        return self.function(context, progress)
