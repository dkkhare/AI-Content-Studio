from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

from backend.version import VERSION


class UpdateDialog(QDialog):
    installerLaunched = Signal(str)

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.release = None
        self.installer_path = ""
        self.setWindowTitle("Application Updates")
        self.resize(620, 480)

        self.current = QLabel(f"Installed version: {VERSION}")
        self.channel = QComboBox()
        self.channel.addItem("Stable releases", "stable")
        self.channel.addItem("Prerelease updates", "prerelease")
        selected = self.channel.findData(self.controller.preferences.channel())
        self.channel.setCurrentIndex(max(0, selected))
        self.auto_check = QCheckBox("Check automatically when the application starts")
        self.auto_check.setChecked(self.controller.preferences.check_on_startup())

        preferences = QHBoxLayout()
        preferences.addWidget(QLabel("Channel:"))
        preferences.addWidget(self.channel, 1)
        preferences.addWidget(self.auto_check)

        self.status = QLabel("Select Check Now to look for updates.")
        self.notes = QTextBrowser()
        self.notes.setPlaceholderText("Release notes will appear here.")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        self.check_button = QPushButton("Check Now")
        self.download_button = QPushButton("Download Verified Installer")
        self.cancel_button = QPushButton("Cancel Download")
        self.install_button = QPushButton("Install Update")
        self.download_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.install_button.setEnabled(False)

        actions = QHBoxLayout()
        actions.addWidget(self.check_button)
        actions.addWidget(self.download_button)
        actions.addWidget(self.cancel_button)
        actions.addWidget(self.install_button)

        close_buttons = QDialogButtonBox(QDialogButtonBox.Close)
        close_buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.current)
        layout.addLayout(preferences)
        layout.addWidget(self.status)
        layout.addWidget(self.notes, 1)
        layout.addWidget(self.progress)
        layout.addLayout(actions)
        layout.addWidget(close_buttons)

        self.channel.currentIndexChanged.connect(self._save_channel)
        self.auto_check.toggled.connect(
            self.controller.preferences.set_check_on_startup
        )
        self.check_button.clicked.connect(self.check)
        self.download_button.clicked.connect(self.download)
        self.cancel_button.clicked.connect(self.controller.cancel)
        self.install_button.clicked.connect(self.install)

        self.controller.checkStarted.connect(self._check_started)
        self.controller.checkFinished.connect(self._check_finished)
        self.controller.checkFailed.connect(self._check_failed)
        self.controller.downloadStarted.connect(self._download_started)
        self.controller.downloadProgress.connect(self._download_progress)
        self.controller.downloadFinished.connect(self._download_finished)
        self.controller.downloadFailed.connect(self._download_failed)
        self.controller.downloadCancelled.connect(self._download_cancelled)
        self.controller.idle.connect(self._refresh)

    def _save_channel(self):
        self.controller.preferences.set_channel(self.channel.currentData())

    def check(self):
        try:
            self.controller.start_check()
        except Exception as exc:
            self._check_failed(str(exc))

    def _check_started(self):
        self.release = None
        self.installer_path = ""
        self.notes.clear()
        self.status.setText("Checking for updates...")
        self.progress.setRange(0, 0)
        self._refresh()

    def _check_finished(self, release):
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.release = release
        if release is None:
            self.status.setText("You are using the latest available version.")
            self.notes.setPlainText("")
        else:
            self.status.setText(f"Version {release.version} is available.")
            self.notes.setMarkdown(release.notes or "No release notes were provided.")
        self._refresh()

    def _check_failed(self, message):
        self.progress.setRange(0, 100)
        self.status.setText(f"Update check failed: {message}")
        self._refresh()

    def download(self):
        if self.release is None:
            return
        try:
            self.controller.start_download(self.release)
        except Exception as exc:
            self._download_failed(str(exc))

    def _download_started(self):
        self.installer_path = ""
        self.status.setText("Downloading and verifying installer...")
        self.progress.setRange(0, 0)
        self._refresh()

    def _download_progress(self, written, total):
        if total > 0:
            self.progress.setRange(0, 100)
            self.progress.setValue(min(100, round(written * 100 / total)))
        else:
            self.progress.setRange(0, 0)

    def _download_finished(self, output):
        self.installer_path = str(output)
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.status.setText(
            f"Verified installer ready: {Path(output).name}"
        )
        self._refresh()

    def _download_failed(self, message):
        self.progress.setRange(0, 100)
        self.status.setText(f"Update download failed: {message}")
        self._refresh()

    def _download_cancelled(self):
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.status.setText("Update download cancelled.")
        self._refresh()

    def install(self):
        if not self.installer_path:
            return
        answer = QMessageBox.question(
            self,
            "Install Update",
            "The application will launch the verified installer and close. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        try:
            self.controller.launch_installer(
                self.installer_path,
                confirmed=True,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Install Update", str(exc))
            return
        self.installerLaunched.emit(self.installer_path)
        QApplication.instance().quit()

    def _refresh(self):
        running = self.controller.is_running()
        self.channel.setEnabled(not running)
        self.auto_check.setEnabled(not running)
        self.check_button.setEnabled(not running)
        self.download_button.setEnabled(not running and self.release is not None)
        self.cancel_button.setEnabled(running and self.installer_path == "")
        self.install_button.setEnabled(not running and bool(self.installer_path))
