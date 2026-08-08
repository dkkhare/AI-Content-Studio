from PySide6.QtWidgets import QApplication

from backend.runtime import resource_path


class ThemeManager:
    """Loads and applies Qt stylesheets."""

    DARK_STYLESHEET = "desktop/themes/dark.qss"

    @classmethod
    def load_dark(cls, app: QApplication):
        qss_file = resource_path(cls.DARK_STYLESHEET)
        if not qss_file.is_file():
            raise FileNotFoundError(f"Required theme resource is missing: {qss_file}")
        app.setStyleSheet(qss_file.read_text(encoding="utf-8"))
