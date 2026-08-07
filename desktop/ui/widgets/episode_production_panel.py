from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from backend.knowledge import KnowledgeStore


class EpisodeProductionPanel(QWidget):
    """Project-level controls and status for final local episode production."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = None
        self.enabled = QCheckBox("Enable final YouTube-ready episode production", self)
        self.subtitles = QCheckBox("Generate Hindi subtitles", self)
        self.burn_subtitles = QCheckBox("Burn subtitles into final video", self)
        self.music_enabled = QCheckBox("Mix background music", self)
        self.music_path = QLineEdit(self)
        self.music_volume = QDoubleSpinBox(self)
        self.music_volume.setRange(0.0, 1.0)
        self.music_volume.setSingleStep(0.01)
        self.music_volume.setDecimals(2)
        self.intro_path = QLineEdit(self)
        self.outro_path = QLineEdit(self)
        self.watermark_enabled = QCheckBox("Overlay channel watermark", self)
        self.watermark_path = QLineEdit(self)
        self.thumbnail_path = QLineEdit(self)
        self.save_button = QPushButton("Save Production Settings", self)
        self.refresh_button = QPushButton("Refresh Status", self)
        self.status = QLabel("Open a project to configure episode production.", self)
        self.status.setWordWrap(True)
        self.save_button.clicked.connect(self.save_settings)
        self.refresh_button.clicked.connect(self.refresh)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(self.enabled)

        box = QGroupBox("Episode Branding and Audio", self)
        form = QFormLayout(box)
        form.addRow(self.subtitles)
        form.addRow(self.burn_subtitles)
        form.addRow(self.music_enabled)
        form.addRow("Background music file", self.music_path)
        form.addRow("Background music volume", self.music_volume)
        form.addRow("Intro video file", self.intro_path)
        form.addRow("Outro video file", self.outro_path)
        form.addRow(self.watermark_enabled)
        form.addRow("Watermark image", self.watermark_path)
        form.addRow("Thumbnail image override", self.thumbnail_path)
        layout.addWidget(box)

        buttons = QHBoxLayout()
        buttons.addWidget(self.save_button)
        buttons.addWidget(self.refresh_button)
        buttons.addStretch()
        layout.addLayout(buttons)
        layout.addWidget(self.status)
        layout.addStretch()

    def set_project(self, project) -> None:
        self.project = project
        self._load_settings()
        self.refresh()

    def _load_settings(self) -> None:
        if self.project is None:
            return
        get = self.project.get_setting
        self.enabled.setChecked(bool(get("pipeline_episode_production_enabled", True)))
        self.subtitles.setChecked(bool(get("production_subtitles_enabled", True)))
        self.burn_subtitles.setChecked(bool(get("production_burn_subtitles", True)))
        self.music_enabled.setChecked(bool(get("background_music_enabled", False)))
        self.music_path.setText(str(get("background_music_path", "") or ""))
        self.music_volume.setValue(float(get("background_music_volume", 0.12)))
        self.intro_path.setText(str(get("channel_intro_path", "") or ""))
        self.outro_path.setText(str(get("channel_outro_path", "") or ""))
        self.watermark_enabled.setChecked(bool(get("channel_watermark_enabled", False)))
        self.watermark_path.setText(str(get("channel_watermark_path", "") or ""))
        self.thumbnail_path.setText(str(get("channel_thumbnail_path", "") or ""))

    def save_settings(self) -> None:
        if self.project is None:
            return
        self.project.update_settings({
            "pipeline_episode_production_enabled": self.enabled.isChecked(),
            "production_subtitles_enabled": self.subtitles.isChecked(),
            "production_burn_subtitles": self.burn_subtitles.isChecked(),
            "background_music_enabled": self.music_enabled.isChecked(),
            "background_music_path": self.music_path.text().strip(),
            "background_music_volume": float(self.music_volume.value()),
            "channel_intro_path": self.intro_path.text().strip(),
            "channel_outro_path": self.outro_path.text().strip(),
            "channel_watermark_enabled": self.watermark_enabled.isChecked(),
            "channel_watermark_path": self.watermark_path.text().strip(),
            "channel_thumbnail_path": self.thumbnail_path.text().strip(),
        })
        self.status.setText("Production settings saved for this project.")

    def refresh(self) -> None:
        if self.project is None:
            return
        store = KnowledgeStore(self.project.root)
        store.initialize()
        assets = [item for item in store.read("assets") if isinstance(item, dict)]
        subtitles = sum(1 for item in assets if item.get("asset_type") == "episode_subtitles")
        thumbnails = sum(1 for item in assets if item.get("asset_type") == "episode_thumbnail")
        exports = sum(1 for item in assets if item.get("asset_type") == "youtube_export")
        self.status.setText(
            f"Production outputs: {exports} YouTube export(s) • "
            f"{subtitles} subtitle file(s) • {thumbnails} thumbnail(s)."
        )

    def clear(self) -> None:
        self.project = None
        self.status.setText("Open a project to configure episode production.")
