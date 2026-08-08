from __future__ import annotations

from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class AIWorkerSignals(QObject):
    chunk = Signal(str)
    finished = Signal(dict)
    failed = Signal(str)
    cancelled = Signal()


class AIStreamWorker(QRunnable):
    """Run provider streaming outside the GUI thread."""

    def __init__(self, controller, *, prompt, provider, model, template=""):
        super().__init__()
        self.controller = controller
        self.prompt = prompt
        self.provider = provider
        self.model = model
        self.template = template
        self.signals = AIWorkerSignals()

    @Slot()
    def run(self):
        usage = None
        try:
            if self.template:
                stream = self.controller.stream_prompt(
                    self.template,
                    self.prompt,
                    provider=self.provider,
                    model=self.model,
                )
            else:
                stream = self.controller.stream(
                    self.prompt,
                    provider=self.provider,
                    model=self.model,
                )
            for chunk in stream:
                if self.controller.cancelled:
                    self.signals.cancelled.emit()
                    return
                if chunk.text:
                    self.signals.chunk.emit(chunk.text)
                if chunk.usage is not None:
                    usage = chunk.usage
            if self.controller.cancelled:
                self.signals.cancelled.emit()
                return
            self.signals.finished.emit({
                "input_tokens": getattr(usage, "input_tokens", 0),
                "output_tokens": getattr(usage, "output_tokens", 0),
                "total_tokens": getattr(usage, "total_tokens", 0),
            })
        except Exception as exc:
            self.signals.failed.emit(str(exc))
