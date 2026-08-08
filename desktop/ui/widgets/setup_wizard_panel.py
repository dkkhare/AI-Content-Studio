from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from backend.readiness import ReadinessService


class SetupWizardPanel(QWidget):
    """Interactive local-first setup editor for project runtime dependencies."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = None
        self.ai_provider = QComboBox(self)
        self.ai_provider.addItems(["ollama"])
        self.ollama_url = QLineEdit(self)
        self.ai_model = QComboBox(self)
        self.ai_model.setEditable(True)
        self.ffmpeg_path = QLineEdit(self)
        self.f5tts_executable = QLineEdit(self)
        self.reference_voice = QLineEdit(self)
        self.image_enabled = QCheckBox("Enable local image generation", self)
        self.image_provider = QComboBox(self)
        self.image_provider.addItems(["local_cli", "comfyui"])
        self.image_executable = QLineEdit(self)
        self.comfyui_workflow = QLineEdit(self)
        self.video_enabled = QCheckBox("Enable local video generation", self)
        self.video_executable = QLineEdit(self)
        self.youtube_enabled = QCheckBox("Use YouTube publishing", self)
        self.youtube_secrets = QLineEdit(self)
        self.status = QLabel("Open a project to configure local tools.", self)
        self.status.setWordWrap(True)
        self._build_ui()

    @staticmethod
    def _browse_row(edit: QLineEdit, callback) -> QWidget:
        host = QWidget()
        layout = QHBoxLayout(host)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(edit)
        button = QPushButton("Browse…", host)
        button.clicked.connect(callback)
        layout.addWidget(button)
        return host

    def _pick_file(self, edit: QLineEdit, title: str, file_filter: str = "All files (*)") -> None:
        start = edit.text().strip() or str(Path.home())
        value, _ = QFileDialog.getOpenFileName(self, title, start, file_filter)
        if value:
            edit.setText(value)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        ai = QGroupBox("AI / Ollama", self)
        form = QFormLayout(ai)
        form.addRow("Provider", self.ai_provider)
        form.addRow("Ollama URL", self.ollama_url)
        form.addRow("Model", self.ai_model)
        discover = QPushButton("Discover Installed Ollama Models", ai)
        discover.clicked.connect(self.discover_ollama_models)
        form.addRow(discover)
        layout.addWidget(ai)

        media = QGroupBox("Narration & Media Tools", self)
        form = QFormLayout(media)
        form.addRow("FFmpeg", self._browse_row(self.ffmpeg_path, lambda: self._pick_file(self.ffmpeg_path, "Select FFmpeg executable")))
        form.addRow("F5-TTS executable", self._browse_row(self.f5tts_executable, lambda: self._pick_file(self.f5tts_executable, "Select F5-TTS executable")))
        form.addRow("Hindi reference WAV", self._browse_row(self.reference_voice, lambda: self._pick_file(self.reference_voice, "Select Hindi reference voice", "Wave audio (*.wav);;All files (*)")))
        layout.addWidget(media)

        image = QGroupBox("Local Image Generation", self)
        form = QFormLayout(image)
        form.addRow(self.image_enabled)
        form.addRow("Provider", self.image_provider)
        form.addRow("Local CLI executable", self._browse_row(self.image_executable, lambda: self._pick_file(self.image_executable, "Select image generator executable")))
        form.addRow("ComfyUI workflow", self._browse_row(self.comfyui_workflow, lambda: self._pick_file(self.comfyui_workflow, "Select ComfyUI workflow", "JSON (*.json);;All files (*)")))
        layout.addWidget(image)

        video = QGroupBox("Local Video Generation", self)
        form = QFormLayout(video)
        form.addRow(self.video_enabled)
        form.addRow("Wan/LTX/CogVideoX CLI", self._browse_row(self.video_executable, lambda: self._pick_file(self.video_executable, "Select video generator executable")))
        layout.addWidget(video)

        publishing = QGroupBox("Publishing", self)
        form = QFormLayout(publishing)
        form.addRow(self.youtube_enabled)
        form.addRow("YouTube OAuth client secrets", self._browse_row(self.youtube_secrets, lambda: self._pick_file(self.youtube_secrets, "Select YouTube OAuth client secrets", "JSON (*.json);;All files (*)")))
        layout.addWidget(publishing)

        buttons = QHBoxLayout()
        save = QPushButton("Save Setup", self)
        save.clicked.connect(self.save_settings)
        check = QPushButton("Save & Run Readiness Check", self)
        check.clicked.connect(self.save_and_check)
        buttons.addWidget(save)
        buttons.addWidget(check)
        buttons.addStretch()
        layout.addLayout(buttons)
        layout.addWidget(self.status)
        layout.addStretch()

    def set_project(self, project) -> None:
        self.project = project
        self._load_settings()

    def _load_settings(self) -> None:
        if self.project is None:
            return
        get = self.project.get_setting
        self.ai_provider.setCurrentText(str(get("ai_provider", "ollama") or "ollama"))
        self.ollama_url.setText(str(get("ollama_url", "http://127.0.0.1:11434") or ""))
        self.ai_model.setCurrentText(str(get("ai_model", "") or ""))
        self.ffmpeg_path.setText(str(get("ffmpeg_path", "") or ""))
        self.f5tts_executable.setText(str(get("f5tts_executable", "") or ""))
        self.reference_voice.setText(str(get("f5tts_reference_audio", get("reference_voice", "")) or ""))
        self.image_enabled.setChecked(bool(get("pipeline_image_generation_enabled", False)))
        self.image_provider.setCurrentText(str(get("image_provider", "local_cli") or "local_cli"))
        self.image_executable.setText(str(get("image_cli_executable", "") or ""))
        self.comfyui_workflow.setText(str(get("comfyui_workflow_file", "") or ""))
        self.video_enabled.setChecked(bool(get("pipeline_video_enabled", False)))
        self.video_executable.setText(str(get("video_cli_executable", "") or ""))
        self.youtube_enabled.setChecked(str(get("publishing_provider", "manual") or "manual").lower() == "youtube")
        self.youtube_secrets.setText(str(get("youtube_client_secrets_path", "") or ""))
        self.status.setText("Setup loaded. Configure local tools, then run the readiness check.")

    def discover_ollama_models(self) -> None:
        url = self.ollama_url.text().strip().rstrip("/") or "http://127.0.0.1:11434"
        try:
            with urllib.request.urlopen(url + "/api/tags", timeout=3) as response:
                payload = json.loads(response.read().decode("utf-8"))
            models = [str(item.get("name", "")).strip() for item in payload.get("models", []) if item.get("name")]
            current = self.ai_model.currentText().strip()
            self.ai_model.clear()
            self.ai_model.addItems(models)
            if current:
                self.ai_model.setCurrentText(current)
            self.status.setText(f"Ollama connection OK. Found {len(models)} installed model(s).")
        except Exception as exc:
            QMessageBox.warning(self, "Ollama Test Failed", str(exc))

    def save_settings(self) -> bool:
        if self.project is None:
            return False
        self.project.update_settings({
            "ai_provider": self.ai_provider.currentText().strip(),
            "ollama_url": self.ollama_url.text().strip(),
            "ai_model": self.ai_model.currentText().strip(),
            "ffmpeg_path": self.ffmpeg_path.text().strip(),
            "f5tts_executable": self.f5tts_executable.text().strip(),
            "f5tts_reference_audio": self.reference_voice.text().strip(),
            "pipeline_image_generation_enabled": self.image_enabled.isChecked(),
            "image_provider": self.image_provider.currentText().strip(),
            "image_cli_executable": self.image_executable.text().strip(),
            "comfyui_workflow_file": self.comfyui_workflow.text().strip(),
            "pipeline_video_enabled": self.video_enabled.isChecked(),
            "video_cli_executable": self.video_executable.text().strip(),
            "publishing_provider": "youtube" if self.youtube_enabled.isChecked() else "manual",
            "youtube_client_secrets_path": self.youtube_secrets.text().strip(),
        })
        self.status.setText("Setup settings saved in the project. Save the project to persist them to disk.")
        return True

    def save_and_check(self) -> None:
        if not self.save_settings() or self.project is None:
            return
        report = ReadinessService(self.project).run()
        if report.get("ready"):
            self.status.setText(f"READY — 0 blockers, {report.get('warning_count', 0)} optional warning(s).")
        else:
            self.status.setText(
                f"NOT READY — {report.get('blocker_count', 0)} blocker(s), "
                f"{report.get('warning_count', 0)} optional warning(s). Open Setup & Readiness for details."
            )

    def refresh(self) -> None:
        if self.project is not None:
            self._load_settings()

    def clear(self) -> None:
        self.project = None
        self.status.setText("Open a project to configure local tools.")
