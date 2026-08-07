from pathlib import Path

from PySide6.QtWidgets import QApplication


class ThemeManager:
    """Loads and applies application Qt stylesheets."""

    @staticmethod
    def load_dark(app: QApplication) -> None:
        qss_file = Path(__file__).parent / "dark.qss"
        if qss_file.exists():
            app.setStyleSheet(qss_file.read_text(encoding="utf-8"))

    @classmethod
    def load_theme(cls, app: QApplication | None, theme: str) -> None:
        if app is None:
            return

        normalized = str(theme or "dark").strip().lower()
        if normalized == "dark":
            cls.load_dark(app)
        else:
            # Qt uses the platform/default palette when no custom stylesheet
            # is installed, which covers both light and system preferences.
            app.setStyleSheet("")
