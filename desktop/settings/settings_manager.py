from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings


class SettingsManager:
    """
    Central application settings manager.

    Uses Qt QSettings for persistent storage.
    """

    ORGANIZATION = "AIContentStudio"

    APPLICATION = "AIContentStudio"

    def __init__(self):

        self.settings = QSettings(

            self.ORGANIZATION,

            self.APPLICATION,

        )
    # --------------------------------------------------
    # Generic API
    # --------------------------------------------------

    def value(

        self,

        key,

        default=None,

    ):

        return self.settings.value(

            key,

            default,

        )

    def set_value(

        self,

        key,

        value,

    ):

        self.settings.setValue(

            key,

            value,

        )

    def remove(

        self,

        key,

    ):

        self.settings.remove(

            key,

        )

    def contains(

        self,

        key,

    ):

        return self.settings.contains(

            key,

        )

    def sync(self):

        self.settings.sync()
    # --------------------------------------------------
    # Window
    # --------------------------------------------------

    def window_geometry(self):

        return self.value(

            "window/geometry",

        )

    def set_window_geometry(

        self,

        geometry,

    ):

        self.set_value(

            "window/geometry",

            geometry,

        )

    def window_state(self):

        return self.value(

            "window/state",

        )

    def set_window_state(

        self,

        state,

    ):

        self.set_value(

            "window/state",

            state,

        )
    # --------------------------------------------------
    # Workspace
    # --------------------------------------------------

    def last_tab(self):

        return int(

            self.value(

                "workspace/tab",

                0,

            )

        )

    def set_last_tab(

        self,

        index,

    ):

        self.set_value(

            "workspace/tab",

            index,

        )
    # --------------------------------------------------
    # Narration
    # --------------------------------------------------

    def last_voice(self):

        return self.value(

            "tts/voice",

            "",

        )

    def set_last_voice(

        self,

        voice,

    ):

        self.set_value(

            "tts/voice",

            voice,

        )

    def output_directory(self):

        return self.value(

            "tts/output_directory",

            str(

                Path("output/tts")

            ),

        )

    def set_output_directory(

        self,

        directory,

    ):

        self.set_value(

            "tts/output_directory",

            directory,

        )
    # --------------------------------------------------
    # Audio
    # --------------------------------------------------

    def volume(self):

        return float(

            self.value(

                "audio/volume",

                1.0,

            )

        )

    def set_volume(

        self,

        volume,

    ):

        self.set_value(

            "audio/volume",

            float(volume),

        )

    # --------------------------------------------------
    # Theme
    # --------------------------------------------------

    def theme(self):

        return self.value(

            "ui/theme",

            "system",

        )

    def set_theme(

        self,

        theme,

    ):

        self.set_value(

            "ui/theme",

            theme,

        )
    # --------------------------------------------------
    # Recent Files
    # --------------------------------------------------

    def recent_files(self):

        return self.value(

            "recent/files",

            [],

        )

    def set_recent_files(

        self,

        files,

    ):

        self.set_value(

            "recent/files",

            files,

        )

    def add_recent_file(

        self,

        filename,

        limit=10,

    ):

        files = list(

            self.recent_files()

        )

        if filename in files:

            files.remove(

                filename

            )

        files.insert(

            0,

            filename,

        )

        self.set_recent_files(

            files[:limit]

        )
    # --------------------------------------------------
    # Reset
    # --------------------------------------------------

    def clear(self):

        self.settings.clear()

        self.settings.sync()