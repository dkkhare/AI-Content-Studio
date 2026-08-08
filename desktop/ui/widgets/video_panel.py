from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from desktop.controllers.video_controller import VideoDesktopController


class VideoPanel(QWidget):
    """Project video composition and rendering controls."""

    videoRendered = Signal(str)

    def __init__(self, parent=None, *, controller=None):
        super().__init__(parent)
        self.controller = controller or VideoDesktopController(self)
        self._build_ui()
        self._connect()
        self.refresh()

    def _path_row(self, form, label):
        edit = QLineEdit()
        button = QPushButton("Browse...")
        row = QHBoxLayout()
        row.addWidget(edit, 1)
        row.addWidget(button)
        form.addRow(label, row)
        return edit, button

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Video Composer"))
        form = QFormLayout()
        self.visual, self.visual_button = self._path_row(form, "Visual")
        self.audio, self.audio_button = self._path_row(form, "Narration")
        self.subtitles, self.subtitle_button = self._path_row(form, "Subtitles")

        self.duration = QDoubleSpinBox()
        self.duration.setRange(0.1, 24 * 60 * 60)
        self.duration.setDecimals(3)
        self.duration.setSuffix(" seconds")
        form.addRow("Duration", self.duration)

        self.resolution = QComboBox()
        self.resolution.addItems(["1920x1080", "1280x720", "1080x1920"])
        form.addRow("Resolution", self.resolution)

        self.fps = QSpinBox()
        self.fps.setRange(1, 120)
        self.fps.setValue(30)
        form.addRow("Frame rate", self.fps)

        self.burn_subtitles = QCheckBox("Burn project subtitles into video")
        self.burn_subtitles.setChecked(True)
        form.addRow("", self.burn_subtitles)

        self.output, self.output_button = self._path_row(form, "Output MP4")
        layout.addLayout(form)

        actions = QHBoxLayout()
        self.render_button = QPushButton("Render Video")
        self.cancel_button = QPushButton("Cancel")
        actions.addStretch()
        actions.addWidget(self.render_button)
        actions.addWidget(self.cancel_button)
        layout.addLayout(actions)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.status = QLabel("Open a project to compose video.")
        layout.addWidget(self.progress)
        layout.addWidget(self.status)
        layout.addStretch()

    def _connect(self):
        self.visual_button.clicked.connect(self.browse_visual)
        self.audio_button.clicked.connect(self.browse_audio)
        self.subtitle_button.clicked.connect(self.browse_subtitles)
        self.output_button.clicked.connect(self.browse_output)
        self.render_button.clicked.connect(self.render_video)
        self.cancel_button.clicked.connect(self.controller.cancel)
        self.controller.renderStarted.connect(self._started)
        self.controller.renderProgress.connect(self._progress)
        self.controller.renderFinished.connect(self._finished)
        self.controller.renderFailed.connect(self._failed)
        self.controller.renderCancelled.connect(self._cancelled)

    def _browse(self, title, filters, target):
        filename, _ = QFileDialog.getOpenFileName(self, title, "", filters)
        if filename:
            target.setText(filename)

    def browse_visual(self):
        self._browse(
            "Select Visual",
            "Visual Media (*.png *.jpg *.jpeg *.webp *.mp4 *.mov *.mkv *.webm)",
            self.visual,
        )

    def browse_audio(self):
        self._browse(
            "Select Narration", "Audio (*.wav *.mp3 *.flac *.ogg *.m4a)", self.audio
        )

    def browse_subtitles(self):
        self._browse("Select Subtitles", "Subtitles (*.srt *.vtt)", self.subtitles)

    def browse_output(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Video Output", self.output.text() or "video.mp4", "MP4 Video (*.mp4)"
        )
        if filename:
            self.output.setText(filename)

    def set_project(self, project):
        try:
            context = self.controller.set_project(project)
            self.visual.setText(context["visual"])
            self.audio.setText(context["audio"])
            self.subtitles.setText(context["subtitles"])
            self.output.setText(context["output"])
            if context["duration_seconds"] > 0:
                self.duration.setValue(context["duration_seconds"])
            self.status.setText("Project video assets loaded.")
        except Exception as exc:
            self._failed(str(exc))
        self.refresh()

    def settings(self):
        width, height = map(int, self.resolution.currentText().split("x"))
        return {
            "visual": self.visual.text().strip(),
            "audio": self.audio.text().strip(),
            "subtitles": (
                self.subtitles.text().strip()
                if self.burn_subtitles.isChecked()
                else None
            ),
            "duration_seconds": self.duration.value(),
            "width": width,
            "height": height,
            "fps": self.fps.value(),
            "output": self.output.text().strip(),
        }

    def validation_error(self):
        if self.controller.project is None:
            return "Open a project before rendering video."
        for label, value in (("visual", self.visual.text()), ("audio", self.audio.text())):
            if not value.strip() or not Path(value).is_file():
                return f"Select a valid {label} file."
        if self.burn_subtitles.isChecked():
            value = self.subtitles.text().strip()
            if value and not Path(value).is_file():
                return "Select a valid subtitle file or disable subtitle burning."
        if not self.output.text().lower().endswith(".mp4"):
            return "Video output must use the .mp4 extension."
        return ""

    def render_video(self):
        error = self.validation_error()
        if error:
            QMessageBox.warning(self, "Video Composer", error)
            self.status.setText(error)
            return
        try:
            self.controller.start_render(**self.settings())
        except Exception as exc:
            self._failed(str(exc))

    def _started(self):
        self.progress.setValue(0)
        self.status.setText("Rendering video...")
        self.refresh()

    def _progress(self, value):
        self.progress.setValue(round(value))

    def _finished(self, output):
        self.progress.setValue(100)
        self.status.setText(f"Rendered {Path(output).name}.")
        self.videoRendered.emit(output)
        self.refresh()

    def _failed(self, message):
        self.status.setText(str(message))
        self.refresh()

    def _cancelled(self):
        self.status.setText("Video rendering cancelled.")
        self.refresh()

    def refresh(self):
        running = self.controller.is_running()
        has_project = self.controller.project is not None
        self.render_button.setEnabled(has_project and not running)
        self.cancel_button.setEnabled(running)
        for widget in (
            self.visual_button,
            self.audio_button,
            self.subtitle_button,
            self.output_button,
            self.resolution,
            self.fps,
            self.duration,
            self.burn_subtitles,
        ):
            widget.setEnabled(not running)

    def clear(self):
        self.controller.cleanup()
        self.controller.set_project(None)
        for edit in (self.visual, self.audio, self.subtitles, self.output):
            edit.clear()
        self.progress.setValue(0)
        self.status.setText("Open a project to compose video.")
        self.refresh()

    def dispose(self):
        self.clear()
