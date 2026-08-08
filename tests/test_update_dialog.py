from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication, QMessageBox

from backend.updating import SemanticVersion, UpdateRelease
from desktop.ui.dialogs.update_dialog import UpdateDialog


class Preferences:
    def __init__(self):
        self.selected_channel = "stable"
        self.auto = True

    def channel(self):
        return self.selected_channel

    def set_channel(self, value):
        self.selected_channel = value

    def check_on_startup(self):
        return self.auto

    def set_check_on_startup(self, value):
        self.auto = bool(value)


class FakeController(QObject):
    checkStarted = Signal()
    checkFinished = Signal(object)
    checkFailed = Signal(str)
    downloadStarted = Signal()
    downloadProgress = Signal(int, int)
    downloadFinished = Signal(str)
    downloadFailed = Signal(str)
    downloadCancelled = Signal()
    idle = Signal()

    def __init__(self):
        super().__init__()
        self.preferences = Preferences()
        self.running = False
        self.checks = 0
        self.downloads = []
        self.cancelled = 0
        self.launches = []

    def is_running(self):
        return self.running

    def start_check(self):
        self.checks += 1
        self.running = True
        self.checkStarted.emit()

    def start_download(self, release):
        self.downloads.append(release)
        self.running = True
        self.downloadStarted.emit()

    def cancel(self):
        self.cancelled += 1

    def launch_installer(self, path, *, confirmed=False):
        self.launches.append((path, confirmed))


def release():
    return UpdateRelease(
        version=SemanticVersion.parse("0.20.0"),
        tag="v0.20.0",
        name="Release",
        notes="Important fixes",
        page_url="https://github.com/release",
        installer_url="https://github.com/installer",
        checksums_url="https://github.com/checksums",
    )


class UpdateDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_check_release_and_download_states(self):
        controller = FakeController()
        dialog = UpdateDialog(controller)
        dialog.check()
        self.assertEqual(controller.checks, 1)
        self.assertEqual(dialog.operation, "check")
        self.assertFalse(dialog.cancel_button.isEnabled())

        controller.running = False
        controller.checkFinished.emit(release())
        controller.idle.emit()
        self.assertTrue(dialog.download_button.isEnabled())
        self.assertIn("0.20.0", dialog.status.text())
        self.assertIn("Important fixes", dialog.notes.toPlainText())

        dialog.download()
        self.assertEqual(len(controller.downloads), 1)
        self.assertTrue(dialog.cancel_button.isEnabled())
        controller.downloadProgress.emit(5, 10)
        self.assertEqual(dialog.progress.value(), 50)
        dialog.close()

    def test_install_requires_dialog_confirmation(self):
        controller = FakeController()
        dialog = UpdateDialog(controller)
        with tempfile.TemporaryDirectory() as root:
            installer = Path(root) / "installer.exe"
            installer.write_bytes(b"installer")
            dialog._download_finished(str(installer))

            with patch.object(
                QMessageBox, "question", return_value=QMessageBox.No
            ):
                dialog.install()
            self.assertEqual(controller.launches, [])

            with patch.object(
                QMessageBox, "question", return_value=QMessageBox.Yes
            ):
                dialog.install()
            self.assertEqual(
                controller.launches,
                [(str(installer), True)],
            )
        dialog.close()

    def test_preferences_and_cancel_are_forwarded(self):
        controller = FakeController()
        dialog = UpdateDialog(controller)
        dialog.channel.setCurrentIndex(1)
        dialog.auto_check.setChecked(False)
        self.assertEqual(controller.preferences.selected_channel, "prerelease")
        self.assertFalse(controller.preferences.auto)
        dialog.cancel_button.click()
        self.assertEqual(controller.cancelled, 0)
        controller.running = True
        dialog.operation = "download"
        dialog._refresh()
        dialog.cancel_button.click()
        self.assertEqual(controller.cancelled, 1)
        dialog.close()


if __name__ == "__main__":
    unittest.main()
