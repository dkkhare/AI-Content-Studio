class PipelineError(Exception):
    pass


class StageError(PipelineError):
    pass