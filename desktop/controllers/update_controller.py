from __future__ import annotations

import subprocess
from pathlib import Path
from threading import Event

from PySide6.QtCore import QObject, QThread, Signal, Slot

from backend.updating import InstallerDownloader, UpdateCancelled, UpdateService
from desktop.settings import UpdatePreferences


class _CheckWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, service, include_prereleases):
        super().__init__()
        self.service = service
        self.include_prereleases = include_prereleases

    @Slot()
    def run(self):
        try:
            self.finished.emit(
                self.service.check(
                    include_prereleases=self.include_prereleases
                )
            )
        except Exception as exc:
            self.failed.emit(str(exc))


class _DownloadWorker(QObject):
    progress = Signal(int, int)
    finished = Signal(str)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, downloader, release, directory, cancel_event):
        super().__init__()
        self.downloader = downloader
        self.release = release
        self.directory = directory
        self.cancel_event = cancel_event

    @Slot()
    def run(self):
        try:
            output = self.downloader.download(
                self.release,
                self.directory,
                cancel_event=self.cancel_event,
                progress=self.progress.emit,
            )
            self.finished.emit(str(output))
        except UpdateCancelled:
            self.cancelled.emit()
        except Exception as exc:
            self.failed.emit(str(exc))


class UpdateDesktopController(QObject):
    checkStarted = Signal()
    checkFinished = Signal(object)
    checkFailed = Signal(str)
    downloadStarted = Signal()
    downloadProgress = Signal(int, int)
    downloadFinished = Signal(str)
    downloadFailed = Signal(str)
    downloadCancelled = Signal()
    idle = Signal()

    def __init__(
        self,
        parent=None,
        *,
        service=None,
        downloader=None,
        preferences=None,
        launcher=None,
    ):
        super().__init__(parent)
        self.service = service or UpdateService()
        self.downloader = downloader or InstallerDownloader()
        self.preferences = preferences or UpdatePreferences()
        self.launcher = launcher or subprocess.Popen
        self._thread = None
        self._worker = None
        self._cancel_event = None

    def is_running(self):
        return self._thread is not None and self._thread.isRunning()

    def _ensure_idle(self):
        if self.is_running():
            raise RuntimeError("An update operation is already active.")

    def _start(self, worker, terminal_signals):
        self._ensure_idle()
        self._thread = QThread(self)
        self._worker = worker
        worker.moveToThread(self._thread)
        self._thread.started.connect(worker.run)
        for signal in terminal_signals:
            signal.connect(self._thread.quit)
        self._thread.finished.connect(worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._clear)
        self._thread.start()

    @Slot()
    def _clear(self):
        self._thread = None
        self._worker = None
        self._cancel_event = None
        self.idle.emit()

    def start_check(self):
        self._ensure_idle()
        worker = _CheckWorker(
            self.service,
            self.preferences.include_prereleases(),
        )
        worker.finished.connect(self.checkFinished)
        worker.failed.connect(self.checkFailed)
        self.checkStarted.emit()
        self._start(worker, (worker.finished, worker.failed))

    def start_download(self, release, directory=None):
        self._ensure_idle()
        if release is None:
            raise ValueError("Select an update release before downloading.")
        destination = directory or self.preferences.download_directory()
        self._cancel_event = Event()
        worker = _DownloadWorker(
            self.downloader,
            release,
            destination,
            self._cancel_event,
        )
        worker.progress.connect(self.downloadProgress)
        worker.finished.connect(self.downloadFinished)
        worker.failed.connect(self.downloadFailed)
        worker.cancelled.connect(self.downloadCancelled)
        self.downloadStarted.emit()
        self._start(
            worker,
            (worker.finished, worker.failed, worker.cancelled),
        )

    def cancel(self):
        if self._cancel_event is not None:
            self._cancel_event.set()

    def launch_installer(self, path, *, confirmed=False):
        if not confirmed:
            raise PermissionError("Explicit user confirmation is required.")
        installer = Path(path).expanduser().resolve()
        if not installer.is_file():
            raise FileNotFoundError(installer)
        return self.launcher([str(installer)], shell=False)

    def dispose(self, timeout_ms=5000):
        self.cancel()
        if self._thread is not None and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(timeout_ms)
