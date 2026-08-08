from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from desktop.ai.configuration import AIProfile


class AISettingsDialog(QDialog):
    """Configure provider preferences without persisting API keys."""

    def __init__(self, controller, store, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.store = store
        self.setWindowTitle("AI Provider Settings")
        self.setMinimumWidth(520)

        self.provider = QComboBox()
        self.provider.addItems(["ollama", "openai", "gemini"])
        self.model = QComboBox()
        self.model.setEditable(True)
        self.secret = QLineEdit()
        self.secret.setEchoMode(QLineEdit.Password)
        self.secret.setPlaceholderText("Session only — never saved")
        self.failover = QLineEdit()
        self.failover.setPlaceholderText("openai, gemini")
        self.timeout = QSpinBox()
        self.timeout.setRange(1, 600)
        self.timeout.setSuffix(" seconds")
        self.status = QLabel("Not checked")
        self.status.setTextInteractionFlags(Qt.TextSelectableByMouse)

        discover = QPushButton("Discover models")
        discover.clicked.connect(self.discover_models)
        health = QPushButton("Test connection")
        health.clicked.connect(self.test_connection)
        actions = QHBoxLayout()
        actions.addWidget(discover)
        actions.addWidget(health)

        form = QFormLayout()
        form.addRow("Provider", self.provider)
        form.addRow("Model", self.model)
        form.addRow("API key", self.secret)
        form.addRow("Fallback order", self.failover)
        form.addRow("Timeout", self.timeout)
        form.addRow("Status", self.status)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_and_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(actions)
        layout.addWidget(QLabel("API keys are kept only in this running process."))
        layout.addWidget(buttons)

        self.provider.currentTextChanged.connect(self._provider_changed)
        self._load()

    def _load(self):
        profile = self.store.load()
        self.provider.setCurrentText(profile.provider)
        self.model.setCurrentText(profile.model)
        self.failover.setText(", ".join(profile.failover))
        self.timeout.setValue(int(profile.timeout_seconds))
        self._provider_changed(profile.provider)

    def _provider_changed(self, provider):
        env_name = self.store.secret_environment(provider)
        self.secret.setEnabled(bool(env_name))
        if env_name and self.store.has_session_secret(provider):
            self.secret.setPlaceholderText(f"{env_name} is configured for this session")
        elif env_name:
            self.secret.setPlaceholderText(f"Enter {env_name} (session only)")
        else:
            self.secret.setPlaceholderText("Ollama does not require an API key")

    def profile(self):
        return AIProfile(
            provider=self.provider.currentText(),
            model=self.model.currentText(),
            failover=[item.strip() for item in self.failover.text().split(",") if item.strip()],
            timeout_seconds=float(self.timeout.value()),
        ).normalized()

    def _apply_session_secret(self):
        if self.secret.isEnabled() and self.secret.text():
            self.store.set_session_secret(self.provider.currentText(), self.secret.text())
            self.secret.clear()

    def test_connection(self):
        try:
            self._apply_session_secret()
            profile = self.controller.configure(self.profile())
            ok, detail = self.controller.health_check(profile.provider)
            self.status.setText(("Connected: " if ok else "Unavailable: ") + detail)
        except Exception as exc:
            self.status.setText(f"Error: {exc}")

    def discover_models(self):
        try:
            self._apply_session_secret()
            profile = self.controller.configure(self.profile())
            models = self.controller.discover_models(profile.provider)
            current = self.model.currentText()
            self.model.clear()
            self.model.addItems(models)
            if current and current not in models:
                self.model.addItem(current)
                self.model.setCurrentText(current)
            self.status.setText(f"Found {len(models)} model(s)")
        except Exception as exc:
            QMessageBox.warning(self, "Model discovery failed", str(exc))

    def save_and_accept(self):
        try:
            self._apply_session_secret()
            profile = self.store.save(self.profile())
            self.controller.configure(profile)
            self.accept()
        except Exception as exc:
            QMessageBox.warning(self, "Unable to save AI settings", str(exc))
