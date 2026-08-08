from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from desktop.ui.main_window import MainWindow


class DesktopAIQtSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_main_window_builds_ai_settings_and_workbench(self):
        window = MainWindow()
        try:
            self.assertIsNotNone(window.ai_controller)
            self.assertIsNotNone(window.aiAssistantDock)
            self.assertFalse(window.aiAssistantDock.isVisible())
            window.show_ai_workbench()
            self.assertFalse(window.aiAssistantDock.generate_button.isEnabled() is False)
            self.assertGreaterEqual(window.aiAssistantDock.template.count(), 1)
            self.assertTrue(hasattr(window, "aiSettingsAction"))
            self.assertTrue(hasattr(window, "aiWorkbenchAction"))
        finally:
            window.close()


if __name__ == "__main__":
    unittest.main()
