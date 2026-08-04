from dataclasses import dataclass


@dataclass
class InstallProgress:

    model: str

    percent: int

    speed: str

    eta: str