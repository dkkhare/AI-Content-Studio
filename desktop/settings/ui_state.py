from __future__ import annotations

from .settings_manager import SettingsManager


class UIState:
    """
    Saves/restores application UI state.
    """

    def __init__(self):

        self.settings = SettingsManager()
    # --------------------------------------------------
    # Main Window
    # --------------------------------------------------

    def save_main_window(

        self,

        window,

    ):

        self.settings.set_window_geometry(

            window.saveGeometry()

        )

        self.settings.set_window_state(

            window.saveState()

        )

        self.settings.sync()

    def restore_main_window(

        self,

        window,

    ):

        geometry = self.settings.window_geometry()

        if geometry:

            window.restoreGeometry(

                geometry

            )

        state = self.settings.window_state()

        if state:

            window.restoreState(

                state

            )
    # --------------------------------------------------
    # Workspace
    # --------------------------------------------------

    def save_workspace(

        self,

        workspace,

    ):

        self.settings.set_last_tab(

            workspace.current_tab()

        )

        self.settings.sync()

    def restore_workspace(

        self,

        workspace,

    ):

        workspace.set_current_tab(

            self.settings.last_tab()

        )
    # --------------------------------------------------
    # Narration
    # --------------------------------------------------

    def save_narration(

        self,

        narration,

    ):

        self.settings.set_last_voice(

            narration.selected_voice()

        )

        self.settings.set_output_directory(

            narration.output_path()

        )

        self.settings.sync()

    def restore_narration(

        self,

        narration,

    ):

        narration.set_output_directory(

            self.settings.output_directory()

        )

        voice = self.settings.last_voice()

        if voice:

            index = narration.voice_combo.findText(

                voice

            )

            if index >= 0:

                narration.voice_combo.setCurrentIndex(

                    index

                )
    # --------------------------------------------------
    # Audio
    # --------------------------------------------------

    def save_audio(

        self,

        player,

    ):

        self.settings.set_volume(

            player.volume()

        )

        self.settings.sync()

    def restore_audio(

        self,

        player,

    ):

        player.set_volume(

            self.settings.volume()

        )
    # --------------------------------------------------
    # Theme
    # --------------------------------------------------

    def theme(self):

        return self.settings.theme()

    def set_theme(

        self,

        theme,

    ):

        self.settings.set_theme(

            theme

        )

        self.settings.sync()