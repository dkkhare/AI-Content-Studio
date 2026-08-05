from dataclasses import dataclass


@dataclass
class PlaybackProgress:

    position: int = 0

    duration: int = 0

    percent: int = 0

    state: str = "Stopped"