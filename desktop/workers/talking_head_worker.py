from __future__ import annotations

from pathlib import Path
from threading import Event

from PySide6.QtCore import QObject, Signal, Slot

from backend.talking_head import (
    BookImporter,
    LongFormTalkingHeadPipeline,
    SadTalkerAdapter,
    SadTalkerConfig,
    SeriesRequest,
    TalkingHeadSeriesPipeline,
)
from backend.tts.adapters import F5TTSAdapter


class TalkingHeadWorker(QObject):
    started = Signal()
    progress = Signal(float, str)
    finished = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, *, pipeline_factory=None, importer=None):
        super().__init__()
        self.pipeline_factory = pipeline_factory
        self.importer = importer or BookImporter()
        self.settings = None
        self.cancel_event = Event()

    def configure(self, **settings):
        self.settings = dict(settings)

    def request_cancel(self):
        self.cancel_event.set()

    def _pipeline(self, settings):
        if self.pipeline_factory:
            return self.pipeline_factory(settings)
        tts = F5TTSAdapter()
        sadtalker = SadTalkerAdapter(
            SadTalkerConfig(
                repository=Path(settings["sadtalker_directory"]),
                python=settings["sadtalker_python"],
                size=settings.get("size", 256),
                preprocess=settings.get("preprocess", "crop"),
                still=settings.get("still", False),
                enhancer=settings.get("enhancer", ""),
            )
        )
        return TalkingHeadSeriesPipeline(
            LongFormTalkingHeadPipeline(tts=tts, sadtalker=sadtalker)
        )

    @Slot()
    def run(self):
        if not self.settings:
            self.failed.emit("Talking-head worker was not configured.")
            return
        self.started.emit()
        try:
            settings = self.settings
            imported = self.importer.import_book(settings["book"])
            request = SeriesRequest(
                blocks=imported.blocks,
                portrait=Path(settings["portrait"]),
                reference_audio=Path(settings["reference_audio"]),
                reference_text=settings["reference_text"],
                output_directory=Path(settings["output_directory"]),
                work_directory=Path(settings["work_directory"]),
                episode_minutes=settings["episode_minutes"],
                segment_seconds=settings["segment_seconds"],
                words_per_minute=settings["words_per_minute"],
                rights_confirmed=settings["rights_confirmed"],
            )
            result = self._pipeline(settings).run(
                request,
                progress=self.progress.emit,
                cancel_event=self.cancel_event,
            )
            if self.cancel_event.is_set():
                self.cancelled.emit()
            else:
                self.finished.emit(result)
        except Exception as exc:
            if self.cancel_event.is_set():
                self.cancelled.emit()
            else:
                self.failed.emit(str(exc))
