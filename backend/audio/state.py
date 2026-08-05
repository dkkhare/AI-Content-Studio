from enum import Enum


class PlaybackState(str, Enum):

    STOPPED = "Stopped"

    PLAYING = "Playing"

    PAUSED = "Paused"

    LOADING = "Loading"

    ERROR = "Error"