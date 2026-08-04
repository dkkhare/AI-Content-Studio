from dataclasses import dataclass


@dataclass
class AIModel:

    name: str

    version: str

    installed: bool = False

    path: str = ""

    size: int = 0