class PipelineError(Exception):
    """Base error for processing-pipeline failures."""


class StageError(PipelineError):
    """Raised when a pipeline stage cannot complete."""


class PipelineCancelled(PipelineError):
    """Raised when a running pipeline is cancelled."""


class PipelineBusyError(PipelineError):
    """Raised when starting work while a runner is already active."""
