from __future__ import annotations

from typing import Dict

from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
)


class WorkflowPanel(QWidget):
    """
    Displays AI Content Studio processing pipeline.

    Shows:
    - Pipeline stages
    - Current active stage
    - Completion state
    - Error state
    - Progress updates
    """

    stageChanged = Signal(str)

    workflowCompleted = Signal()

    workflowFailed = Signal(str)


    def __init__(
        self,
        parent=None,
    ):

        super().__init__(parent)

        self.current_stage = None

        self.stage_labels: Dict[str, QLabel] = {}

        self.stage_states = {}

        self._build_ui()


    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def _build_ui(
        self,
    ):

        main = QVBoxLayout(
            self
        )

        main.setSpacing(
            8
        )


        title = QLabel(
            "<h2>AI Processing Pipeline</h2>"
        )

        main.addWidget(
            title
        )


        self.status_label = QLabel(
            "Ready"
        )

        main.addWidget(
            self.status_label
        )


        stages = [

            "PDF Import",

            "OCR",

            "Text Cleanup",

            "Voice Generation",

            "Avatar Animation",

            "Subtitle Sync",

            "Video Render",

        ]


        for stage in stages:

            row = QHBoxLayout()


            label = QLabel(
                stage
            )

            status = QLabel(
                "Pending"
            )


            row.addWidget(
                label
            )

            row.addStretch()

            row.addWidget(
                status
            )


            container = QWidget()

            container.setLayout(
                row
            )


            main.addWidget(
                container
            )


            self.stage_labels[stage] = status

            self.stage_states[stage] = "pending"


        self.reset_button = QPushButton(
            "Reset"
        )


        self.reset_button.clicked.connect(
            self.reset
        )


        main.addWidget(
            self.reset_button
        )


        main.addStretch()
    # --------------------------------------------------
    # Workflow Control
    # --------------------------------------------------

    def set_stage(
        self,
        stage: str,
    ):
        """
        Mark current active processing stage.
        """

        if stage not in self.stage_labels:

            return


        self.current_stage = stage


        for name, label in self.stage_labels.items():

            if name == stage:

                label.setText(
                    "▶ Running"
                )

            else:

                label.setText(
                    "Waiting"
                )


        self.stageChanged.emit(
            stage
        )


    def complete_stage(
        self,
        stage: str,
    ):
        """
        Mark a stage as completed.
        """

        if stage in self.stage_labels:

            self.stage_labels[stage].setText(
                "✓ Completed"
            )


    def fail_stage(
        self,
        stage: str,
        message: str = "Failed",
    ):
        """
        Mark stage as failed.
        """

        if stage in self.stage_labels:

            self.stage_labels[stage].setText(
                f"✗ {message}"
            )


    def update_status(
        self,
        stage: str,
        status: str,
    ):
        """
        Generic status update.
        """

        if stage in self.stage_labels:

            self.stage_labels[stage].setText(
                status
            )


    # --------------------------------------------------
    # Refresh
    # --------------------------------------------------

    def refresh(
        self,
    ):
        """
        Refresh workflow display.

        Called by Dashboard / Workspace.
        """

        if self.current_stage:

            self.set_stage(
                self.current_stage
            )


    # --------------------------------------------------
    # Reset
    # --------------------------------------------------

    def reset(
        self,
    ):
        """
        Reset all workflow stages.
        """

        self.current_stage = None


        for label in self.stage_labels.values():

            label.setText(
                "Waiting"
            )


        self.workflowReset.emit()


    # --------------------------------------------------
    # Information
    # --------------------------------------------------

    def current(
        self,
    ):
        """
        Return active stage.
        """

        return self.current_stage


    def status(
        self,
        stage: str,
    ):
        """
        Return stage status.
        """

        if stage in self.stage_labels:

            return self.stage_labels[stage].text()


        return None