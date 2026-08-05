from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import (
    QObject,
    QUrl,
    Signal,
)

from PySide6.QtMultimedia import (
    QAudioOutput,
    QMediaPlayer,
)

from backend.audio.exception import AudioPlayerError
from backend.audio.progress import PlaybackProgress
from backend.audio.state import PlaybackState


class AudioPlayer(QObject):
    """
    Audio playback wrapper around QMediaPlayer.
    """

    # ------------------------------------------
    # Signals
    # ------------------------------------------

    started = Signal()

    paused = Signal()

    stopped = Signal()

    finished = Signal()

    positionChanged = Signal(object)

    durationChanged = Signal(int)

    stateChanged = Signal(str)

    errorOccurred = Signal(str)

    # ------------------------------------------

    def __init__(self, parent=None):

        super().__init__(parent)

        self.player = QMediaPlayer(self)

        self.audio_output = QAudioOutput(self)

        self.player.setAudioOutput(
            self.audio_output
        )

        self.state = PlaybackState.STOPPED

        self.current_file = None

        self._connect_signals()
    # ------------------------------------------
    # Signal Connections
    # ------------------------------------------

    def _connect_signals(self):

        self.player.positionChanged.connect(

            self._position_changed

        )

        self.player.durationChanged.connect(

            self._duration_changed

        )

        self.player.playbackStateChanged.connect(

            self._playback_state_changed

        )

        self.player.errorOccurred.connect(

            self._error_occurred

        )

        self.player.mediaStatusChanged.connect(

            self._media_status_changed

        )
    # ------------------------------------------
    # Playback
    # ------------------------------------------

    def play(

        self,

        filename,

    ):

        path = Path(filename)

        if not path.exists():

            raise AudioPlayerError(

                f"Audio file not found: {filename}"

            )

        self.current_file = str(path)

        self.player.setSource(

            QUrl.fromLocalFile(

                str(path)

            )

        )

        self.player.play()

    # ------------------------------------------

    def pause(self):

        self.player.pause()

    # ------------------------------------------

    def resume(self):

        self.player.play()

    # ------------------------------------------

    def stop(self):

        self.player.stop()
    # ------------------------------------------
    # Volume
    # ------------------------------------------

    def volume(self):

        return self.audio_output.volume()

    def set_volume(

        self,

        value,

    ):

        value = max(

            0.0,

            min(

                1.0,

                float(value),

            ),

        )

        self.audio_output.setVolume(value)

    # ------------------------------------------

    def mute(self):

        self.audio_output.setMuted(True)

    def unmute(self):

        self.audio_output.setMuted(False)

    def is_muted(self):

        return self.audio_output.isMuted()
    # ------------------------------------------
    # Information
    # ------------------------------------------

    def current_position(self):

        return self.player.position()

    def duration(self):

        return self.player.duration()

    def playback_state(self):

        return self.state

    def source(self):

        return self.current_file