from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
)


class WorkflowPanel(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

        title = QLabel("<h2>AI Processing Pipeline</h2>")

        layout.addWidget(title)

        stages = [
            "📄 PDF Import",
            "🔍 OCR",
            "🧹 Text Cleanup",
            "🎤 Voice Generation",
            "🙂 Avatar Animation",
            "📝 Subtitle Sync",
            "🎬 Video Render",
        ]

        for stage in stages:
            layout.addWidget(QLabel(stage))

        layout.addStretch()