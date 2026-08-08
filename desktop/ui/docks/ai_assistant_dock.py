from __future__ import annotations

from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import (
    QComboBox,
    QDockWidget,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from desktop.workers.ai_stream_worker import AIStreamWorker


class AIAssistantDock(QDockWidget):
    """Interactive AI prompt workbench with background streaming."""

    def __init__(self, controller, parent=None):
        super().__init__("AI Workbench", parent)
        self.controller = controller
        self.thread_pool = QThreadPool.globalInstance()
        self.worker = None
        self.last_request = None

        body = QWidget()
        self.provider = QComboBox()
        self.model = QComboBox()
        self.model.setEditable(True)
        self.template = QComboBox()
        self.input = QPlainTextEdit()
        self.input.setPlaceholderText("Enter prompt or source text…")
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.status = QLabel("Ready")
        self.usage = QLabel("Tokens: 0")

        self.generate_button = QPushButton("Generate")
        self.cancel_button = QPushButton("Cancel")
        self.retry_button = QPushButton("Retry")
        clear_button = QPushButton("Clear")
        self.cancel_button.setEnabled(False)
        self.retry_button.setEnabled(False)

        self.generate_button.clicked.connect(self.generate)
        self.cancel_button.clicked.connect(self.cancel)
        self.retry_button.clicked.connect(self.retry)
        clear_button.clicked.connect(self.clear)

        form = QFormLayout()
        form.addRow("Provider", self.provider)
        form.addRow("Model", self.model)
        form.addRow("Prompt template", self.template)

        buttons = QHBoxLayout()
        buttons.addWidget(self.generate_button)
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.retry_button)
        buttons.addWidget(clear_button)

        layout = QVBoxLayout(body)
        layout.addLayout(form)
        layout.addWidget(QLabel("Input"))
        layout.addWidget(self.input)
        layout.addLayout(buttons)
        layout.addWidget(QLabel("Output"))
        layout.addWidget(self.output)
        layout.addWidget(self.usage)
        layout.addWidget(self.status)
        self.setWidget(body)
        self.refresh_profile()

    def refresh_profile(self):
        config = self.controller.manager.config
        providers = self.controller.providers()
        current_provider = config.default_provider or (providers[0] if providers else "")
        self.provider.clear()
        self.provider.addItems(providers)
        self.provider.setCurrentText(current_provider)
        self.model.setCurrentText(config.model_for(current_provider))

        current_template = self.template.currentData()
        self.template.clear()
        self.template.addItem("Direct prompt", "")
        for name in self.controller.prompt_names():
            self.template.addItem(name.replace("_", " ").title(), name)
        index = self.template.findData(current_template)
        if index >= 0:
            self.template.setCurrentIndex(index)

    def generate(self):
        prompt = self.input.toPlainText().strip()
        if not prompt:
            self.status.setText("Input is required.")
            return
        request = {
            "prompt": prompt,
            "provider": self.provider.currentText(),
            "model": self.model.currentText().strip(),
            "template": self.template.currentData() or "",
        }
        self.last_request = request
        self.output.clear()
        self.usage.setText("Tokens: pending")
        self._set_running(True)
        self.status.setText("Generating…")

        self.worker = AIStreamWorker(self.controller, **request)
        self.worker.signals.chunk.connect(self._append_chunk)
        self.worker.signals.finished.connect(self._finished)
        self.worker.signals.failed.connect(self._failed)
        self.worker.signals.cancelled.connect(self._cancelled)
        self.thread_pool.start(self.worker)

    def retry(self):
        if not self.last_request:
            return
        self.input.setPlainText(self.last_request["prompt"])
        self.provider.setCurrentText(self.last_request["provider"])
        self.model.setCurrentText(self.last_request["model"])
        index = self.template.findData(self.last_request["template"])
        if index >= 0:
            self.template.setCurrentIndex(index)
        self.generate()

    def cancel(self):
        self.controller.cancel()
        self.status.setText("Cancelling…")

    def clear(self):
        if self.worker is not None:
            self.controller.cancel()
        self.input.clear()
        self.output.clear()
        self.usage.setText("Tokens: 0")
        self.status.setText("Ready")

    def _set_running(self, running):
        self.generate_button.setEnabled(not running)
        self.cancel_button.setEnabled(running)
        self.retry_button.setEnabled(not running and self.last_request is not None)

    def _append_chunk(self, text):
        cursor = self.output.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(text)
        self.output.setTextCursor(cursor)
        self.output.ensureCursorVisible()

    def _finished(self, usage):
        self.worker = None
        self._set_running(False)
        self.usage.setText(
            f"Tokens: {usage.get('total_tokens', 0)} "
            f"(input {usage.get('input_tokens', 0)}, output {usage.get('output_tokens', 0)})"
        )
        self.status.setText("Completed")

    def _failed(self, message):
        self.worker = None
        self._set_running(False)
        self.status.setText(f"Failed: {message}")

    def _cancelled(self):
        self.worker = None
        self._set_running(False)
        self.status.setText("Cancelled")
