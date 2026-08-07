from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from backend.knowledge import ProjectStatusService


class ProjectStatusDashboard(QWidget):
    """Read-only project overview backed by persisted project state."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = None
        self.title = QLabel("Project Overview", self)
        self.title.setTextFormat(Qt.RichText)
        self.summary = QLabel("Open a project to view progress.", self)
        self.summary.setWordWrap(True)
        self.refresh_button = QPushButton("Refresh", self)
        self.refresh_button.clicked.connect(self.refresh)
        self._stage_labels: dict[str, QLabel] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.addWidget(self.title)
        outer.addWidget(self.summary)
        outer.addWidget(self.refresh_button, 0, Qt.AlignLeft)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        body = QWidget(scroll)
        grid = QGridLayout(body)

        stages = (
            ("ocr", "OCR"),
            ("spelling", "Hindi Spelling Review"),
            ("grammar", "Hindi Grammar Review"),
            ("script", "Hindi Podcast Script"),
            ("episodes", "Episode Planning / Review"),
            ("characters", "Character Review"),
            ("locations", "Location Review"),
            ("scenes", "Scene Planning"),
            ("audio", "F5-TTS Episode Audio"),
            ("video", "Episode Video"),
        )
        for index, (key, label) in enumerate(stages):
            box = QGroupBox(label, body)
            layout = QVBoxLayout(box)
            value = QLabel("Not started", box)
            value.setWordWrap(True)
            layout.addWidget(value)
            self._stage_labels[key] = value
            grid.addWidget(box, index // 2, index % 2)

        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

    def set_project(self, project) -> None:
        self.project = project
        self.refresh()

    def clear(self) -> None:
        self.project = None
        self.title.setText("<h2>Project Overview</h2>")
        self.summary.setText("Open a project to view progress.")
        for label in self._stage_labels.values():
            label.setText("Not started")

    @staticmethod
    def _mark(done: bool, done_text: str = "Complete", pending_text: str = "Not started") -> str:
        return f"✓ {done_text}" if done else f"○ {pending_text}"

    def refresh(self) -> None:
        if self.project is None:
            return
        status = ProjectStatusService(self.project).snapshot()
        self.title.setText(f"<h2>{status['project_name']}</h2>")
        self.summary.setText(
            f"Language: {status['language']}  •  "
            f"Episodes: {status['episodes_planned']} planned, "
            f"{status['episodes_approved']} approved, "
            f"{status['episodes_pending']} pending"
        )
        self._stage_labels["ocr"].setText(self._mark(status["ocr"], "OCR complete"))
        self._stage_labels["spelling"].setText(
            self._mark(status["spelling"], "Spelling correction saved", "Optional / not run")
        )
        self._stage_labels["grammar"].setText(
            self._mark(status["grammar"], "Grammar correction saved", "Optional / not run")
        )
        self._stage_labels["script"].setText(
            self._mark(status["script"], "Podcast script ready")
        )
        if status["episodes_planned"]:
            self._stage_labels["episodes"].setText(
                f"{status['episodes_planned']} planned • "
                f"{status['episodes_approved']} approved • "
                f"{status['episodes_skipped']} skipped • "
                f"{status['episodes_pending']} pending"
            )
        else:
            self._stage_labels["episodes"].setText("○ Not planned")

        self._stage_labels["characters"].setText(
            f"{status['character_count']} known • {status['characters_pending']} pending approval"
        )
        self._stage_labels["locations"].setText(
            f"{status['location_count']} known • {status['locations_pending']} pending approval"
        )
        self._stage_labels["scenes"].setText(
            f"{status['scene_count']} scene(s) planned" if status["scene_count"] else "○ Not planned"
        )
        self._stage_labels["audio"].setText(
            f"{status['audio_episode_count']} episode(s) generated"
            if status["audio_episode_count"] else "○ Not generated"
        )
        self._stage_labels["video"].setText(
            f"{status['video_episode_count']} episode(s) generated"
            if status["video_episode_count"] else "○ Not generated"
        )
