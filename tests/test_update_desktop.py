from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QEventLoop, QTimer

from backend.updating import SemanticVersion, UpdateRelease
from desktop.controllers.update_controller import UpdateDesktopController
from desktop.settings import UpdatePreferences


class MemorySettings:
    def __init__(self, values=None):
        self.values = dict(values or {})
        self.syncs = 0

    def value(self, key, default=None):
        return self.values.get(key, default)

    def set_value(self, key, value):
        self.values[key] = value

    def sync(self):
        self.syncs += 1


def release():
    return UpdateRelease(
        version=SemanticVersion.parse("0.20.0"),
        tag="v0.20.0",
        name="Release",
        notes="Changes",
        page_url="https://github.com/release",
        installer_url="https://github.com/installer",
        checksums_url="https://github.com/checksums",
    )


class UpdatePreferenceTests(unittest.TestCase):
    def test_defaults_validation_and_persistence(self):
        settings = MemorySettings()
        preferences = UpdatePreferences(settings)
        self.assertEqual(preferences.channel(), "stable")
        self.assertTrue(preferences.check_on_startup())
        self.assertFalse(preferences.include_prereleases())

        preferences.set_channel("prerelease")
        preferences.set_check_on_startup(False)
        preferences.set_download_directory("downloads")
        self.assertTrue(preferences.include_prereleases())
        self.assertFalse(preferences.check_on_startup())
        self.assertEqual(preferences.download_directory(), "downloads")
        self.assertEqual(settings.syncs, 3)
        with self.assertRaises(ValueError):
            preferences.set_channel("nightly")
        with self.assertRaises(ValueError):
            preferences.set_download_directory("")

    def test_invalid_persisted_channel_falls_back_to_stable(self):
        preferences = UpdatePreferences(
            MemorySettings({UpdatePreferences.CHANNEL_KEY: "unexpected"})
        )
        self.assertEqual(preferences.channel(), "stable")


class UpdateControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    @staticmethod
    def wait_for(signal, action):
        loop = QEventLoop()
        values = []
        signal.connect(lambda *args: (values.append(args), loop.quit()))
        QTimer.singleShot(3000, loop.quit)
        action()
        loop.exec()
        return values

    def test_background_check_uses_persisted_channel(self):
        calls = []

        class Service:
            def check(self, *, include_prereleases=False):
                calls.append(include_prereleases)
                return release()

        preferences = UpdatePreferences(
            MemorySettings({UpdatePreferences.CHANNEL_KEY: "prerelease"})
        )
        controller = UpdateDesktopController(
            service=Service(), preferences=preferences
        )
        values = self.wait_for(controller.checkFinished, controller.start_check)
        self.assertEqual(values[0][0].tag, "v0.20.0")
        self.assertEqual(calls, [True])
        controller.dispose()

    def test_background_download_reports_progress_and_output(self):
        class Downloader:
            def download(self, selected, directory, cancel_event=None, progress=None):
                output = Path(directory) / "installer.exe"
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(b"installer")
                progress(9, 9)
                return output

        with tempfile.TemporaryDirectory() as root:
            preferences = UpdatePreferences(MemorySettings())
            controller = UpdateDesktopController(
                downloader=Downloader(), preferences=preferences
            )
            progress = []
            controller.downloadProgress.connect(
                lambda written, total: progress.append((written, total))
            )
            values = self.wait_for(
                controller.downloadFinished,
                lambda: controller.start_download(release(), root),
            )
            self.assertTrue(Path(values[0][0]).is_file())
            self.assertEqual(progress, [(9, 9)])
            controller.dispose()

    def test_installer_launch_requires_explicit_confirmation(self):
        calls = []
        controller = UpdateDesktopController(
            launcher=lambda args, shell=False: calls.append((args, shell))
        )
        with tempfile.TemporaryDirectory() as root:
            installer = Path(root) / "installer.exe"
            installer.write_bytes(b"installer")
            with self.assertRaises(PermissionError):
                controller.launch_installer(installer)
            self.assertEqual(calls, [])
            controller.launch_installer(installer, confirmed=True)
            self.assertEqual(calls, [([str(installer.resolve())], False)])


if __name__ == "__main__":
    unittest.main()
