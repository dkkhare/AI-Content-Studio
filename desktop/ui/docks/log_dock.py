from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import (
    QDockWidget,
    QTextEdit,
)


class LogDock(QDockWidget):
    """
    Application log console.

    Responsibilities:
    - Display application logs
    - Provide timestamped messages
    - Support clearing logs

    Logging generation remains outside this widget.
    """

    def __init__(
        self,
        parent=None,
    ):

        super().__init__(
            "Log Console",
            parent,
        )


        self.console = QTextEdit()

        self.console.setReadOnly(
            True
        )


        self.setWidget(
            self.console
        )


    # --------------------------------------------------
    # Logging
    # --------------------------------------------------

    def log(
        self,
        message: str,
        level: str = "INFO",
    ):

        timestamp = datetime.now().strftime(
            "%H:%M:%S"
        )


        formatted = (
            f"[{timestamp}] "
            f"{level}: "
            f"{message}"
        )


        self.console.append(
            formatted
        )


    def info(
        self,
        message: str,
    ):

        self.log(
            message,
            "INFO",
        )


    def warning(
        self,
        message: str,
    ):

        self.log(
            message,
            "WARNING",
        )


    def error(
        self,
        message: str,
    ):

        self.log(
            message,
            "ERROR",
        )


    # --------------------------------------------------
    # Maintenance
    # --------------------------------------------------

    def clear(
        self,
    ):

        self.console.clear()


    def refresh(
        self,
    ):
        """
        Reserved for future log filtering.
        """

        pass