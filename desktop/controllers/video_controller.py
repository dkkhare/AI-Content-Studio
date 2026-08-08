from __future__ import annotations

import wave
from pathlib import Path
from threading import Event

from PySide6.QtCore import QObject, QThread, Signal, Slot

from backend.video import (
    FFmpegRenderer,
    FFmpegStatus,
    ProjectVideoService,
    RenderCancelled,
)


class _RenderWorker(QObject):
    progress = Signal(float)
    finished = Signal(str)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, renderer, manifest, output, cancel_event):
        super().__init__()
        self.renderer = renderer
        self.manifest = manifest
        self.output = output
        self.cancel_event = cancel_event

    @Slot()
    def run(self):
        try:
            result = self.renderer.render(
                self.manifest,
                self.output,
                progress=self.progress.emit,
                cancel_event=self.cancel_event,
            )
            self.finished.emit(str(result))
        except RenderCancelled:
            self.cancelled.emit()
        except Exception as exc:
            self.failed.emit(str(exc))


class VideoDesktopController(QObject):
    """Project-aware video planning and background rendering facade."""

    renderStarted = Signal()
    renderProgress = Signal(float)
    renderFinished = Signal(str)
    renderFailed = Signal(str)
    renderCancelled = Signal()

    VISUAL_FIELDS = ("cover_image", "thumbnail")
    AUDIO_FIELDS = ("narration_file", "audiobook_file", "podcast_file")
    VISUAL_OUTPUTS = ("output/cover.png", "output/thumbnail.png")

    def __init__(self, parent=None, *, service=None, renderer=None):
        super().__init__(parent)
        self.service = service or ProjectVideoService()
        self.renderer = renderer or FFmpegRenderer()
        self.project = None
        self._thread = None
        self._worker = None
        self._cancel_event = None
        self._renderer_status = None

    def renderer_status(self, *, refresh=False):
        if refresh or self._renderer_status is None:
            preflight = getattr(self.renderer, "preflight", None)
            self._renderer_status = (
                preflight()
                if callable(preflight)
                else FFmpegStatus(True, "custom", version="Custom renderer")
            )
        return self._renderer_status

    def _require_renderer(self):
        return self.renderer_status().require()

    def _project_path(self, value):
        if self.project is None:
            raise RuntimeError("Open a project before rendering video.")
        root = Path(self.project.root).resolve()
        path = Path(str(value))
        if not path.is_absolute():
            path = root / path
        path = path.resolve()
        if path != root and root not in path.parents:
            raise ValueError("Video assets must remain inside the project.")
        return path

    def set_project(self, project):
        if self.is_running():
            raise RuntimeError("Cannot change project while video rendering is active.")
        self.project = project
        return self.project_context()

    def _first_asset(self, fields, fallbacks=()):
        if self.project is None:
            return None
        candidates = [getattr(self.project, name, "") for name in fields]
        candidates.extend(fallbacks)
        for value in candidates:
            if value:
                path = self._project_path(value)
                if path.is_file():
                    return path
        return None

    def visual_asset(self):
        return self._first_asset(self.VISUAL_FIELDS, self.VISUAL_OUTPUTS)

    def audio_asset(self):
        return self._first_asset(self.AUDIO_FIELDS)

    def subtitle_asset(self):
        return self._first_asset(("subtitle_file",))

    def audio_duration_seconds(self, path=None):
        source = Path(path).resolve() if path else self.audio_asset()
        if source is None or not source.is_file():
            return 0.0
        if source.suffix.lower() == ".wav":
            with wave.open(str(source), "rb") as audio:
                rate = audio.getframerate()
                return audio.getnframes() / rate if rate else 0.0
        try:
            import soundfile as sf
            info = sf.info(source)
            return info.frames / info.samplerate if info.samplerate else 0.0
        except Exception:
            return 0.0

    def project_context(self):
        visual = self.visual_asset()
        audio = self.audio_asset()
        subtitles = self.subtitle_asset()
        output = self._project_path("output/video.mp4") if self.project else None
        return {
            "visual": str(visual) if visual else "",
            "audio": str(audio) if audio else "",
            "subtitles": str(subtitles) if subtitles else "",
            "duration_seconds": self.audio_duration_seconds(audio),
            "output": str(output) if output else "",
            "ffmpeg": self.renderer_status(),
        }

    def prepare(
        self,
        *,
        visual,
        audio,
        duration_seconds,
        subtitles=None,
        width=1920,
        height=1080,
        fps=30,
        output="output/video.mp4",
    ):
        if self.project is None:
            raise RuntimeError("Open a project before rendering video.")
        manifest, _ = self.service.create_manifest(
            self.project,
            visual=visual,
            audio=audio,
            subtitles=subtitles or None,
            duration_seconds=duration_seconds,
            width=width,
            height=height,
            fps=fps,
        )
        target = self._project_path(output)
        if target.suffix.lower() != ".mp4":
            raise ValueError("Video output must use the .mp4 extension.")
        return manifest, target

    def _register_success(self, output):
        target = str(Path(output).resolve())
        self.project.add_output_file("video_file", target)
        self.project.complete_processing()
        return target

    def render_sync(self, **settings):
        self._require_renderer()
        manifest, output = self.prepare(**settings)
        self.project.start_processing("video")
        try:
            result = self.renderer.render(manifest, output)
        except Exception as exc:
            if isinstance(exc, RenderCancelled):
                self.project.reset_processing()
            else:
                self.project.set_error(str(exc))
            raise
        return self._register_success(result)

    def start_render(self, **settings):
        if self.is_running():
            raise RuntimeError("Video rendering is already active.")
        self._require_renderer()
        manifest, output = self.prepare(**settings)
        self.project.start_processing("video")
        self._cancel_event = Event()
        self._thread = QThread(self)
        self._worker = _RenderWorker(
            self.renderer, manifest, output, self._cancel_event
        )
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self.renderProgress)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.cancelled.connect(self._on_cancelled)
        for signal in (
            self._worker.finished,
            self._worker.failed,
            self._worker.cancelled,
        ):
            signal.connect(self._thread.quit)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._clear_worker)
        self._thread.start()
        self.renderStarted.emit()

    @Slot(str)
    def _on_finished(self, output):
        self.renderFinished.emit(self._register_success(output))

    @Slot(str)
    def _on_failed(self, message):
        self.project.set_error(message)
        self.renderFailed.emit(message)

    @Slot()
    def _on_cancelled(self):
        self.project.reset_processing()
        self.renderCancelled.emit()

    @Slot()
    def _clear_worker(self):
        self._worker = None
        self._thread = None
        self._cancel_event = None

    def cancel(self):
        if self._cancel_event is not None:
            self._cancel_event.set()

    def is_running(self):
        return self._thread is not None and self._thread.isRunning()

    def cleanup(self):
        self.cancel()
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait(5000)
