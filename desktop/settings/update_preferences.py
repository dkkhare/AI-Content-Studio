from __future__ import annotations

from backend.runtime import app_data_dir

from .settings_manager import SettingsManager


class UpdatePreferences:
    CHANNEL_KEY = "updates/channel"
    AUTO_CHECK_KEY = "updates/check_on_startup"
    DOWNLOAD_DIRECTORY_KEY = "updates/download_directory"

    def __init__(self, settings=None):
        self.settings = settings or SettingsManager()

    @staticmethod
    def _boolean(value, default):
        if isinstance(value, bool):
            return value
        if value is None:
            return default
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    def channel(self):
        value = str(self.settings.value(self.CHANNEL_KEY, "stable")).strip().lower()
        return value if value in {"stable", "prerelease"} else "stable"

    def set_channel(self, channel):
        channel = str(channel).strip().lower()
        if channel not in {"stable", "prerelease"}:
            raise ValueError("Update channel must be stable or prerelease.")
        self.settings.set_value(self.CHANNEL_KEY, channel)
        self.settings.sync()

    def check_on_startup(self):
        return self._boolean(
            self.settings.value(self.AUTO_CHECK_KEY, True),
            True,
        )

    def set_check_on_startup(self, enabled):
        self.settings.set_value(self.AUTO_CHECK_KEY, bool(enabled))
        self.settings.sync()

    def download_directory(self):
        default = str(app_data_dir() / "updates")
        return str(self.settings.value(self.DOWNLOAD_DIRECTORY_KEY, default))

    def set_download_directory(self, directory):
        value = str(directory).strip()
        if not value:
            raise ValueError("Update download directory is required.")
        self.settings.set_value(self.DOWNLOAD_DIRECTORY_KEY, value)
        self.settings.sync()

    def include_prereleases(self):
        return self.channel() == "prerelease"
