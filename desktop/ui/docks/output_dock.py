from __future__ import annotations

from PySide6.QtWidgets import (
    QDockWidget,
    QTextEdit,
)


class OutputDock(QDockWidget):
    """
    Output panel for application results.

    Used for:
    - generated files
    - processing messages
    - pipeline output

    Worker/business logic should not live here.
    """


    def __init__(
        self,
        parent=None,
    ):

        super().__init__(
            "Output",
            parent,
        )


        self.output_view = QTextEdit()


        self.output_view.setReadOnly(
            True
        )


        self.setWidget(
            self.output_view
        )


    # --------------------------------------------------
    # Output Handling
    # --------------------------------------------------

    def append(
        self,
        message: str,
    ):

        self.output_view.append(
            message
        )


    def set_text(
        self,
        text: str,
    ):

        self.output_view.setPlainText(
            text
        )


    def clear(
        self,
    ):

        self.output_view.clear()


    # --------------------------------------------------
    # Pipeline Helpers
    # --------------------------------------------------

    def show_success(
        self,
        message: str,
    ):

        self.append(
            f"SUCCESS: {message}"
        )


    def show_error(
        self,
        message: str,
    ):

        self.append(
            f"ERROR: {message}"
        )


    def refresh(
        self,
    ):
        """
        Reserved for future pipeline refresh.
        """

        pass