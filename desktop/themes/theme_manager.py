from pathlib import Path

from PySide6.QtWidgets import QApplication


class ThemeManager:
    """Loads and applies Qt stylesheets."""

    @staticmethod
    def load_dark(app: QApplication):
        qss_file = Path(__file__).parent / "dark.qss"

        if qss_file.exists():
            app.setStyleSheet(qss_file.read_text(encoding="utf-8"))