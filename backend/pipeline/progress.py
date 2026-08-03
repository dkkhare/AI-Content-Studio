from dataclasses import dataclass


@dataclass
class PipelineProgress:

    current_stage: str = ""

    percent: int = 0

    message: str = ""