from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.project.manager import ProjectManager
from backend.project.serializer import ProjectSerializer


class ProjectLifecycleSmokeTests(unittest.TestCase):
    def test_create_save_reload_settings_recovery_and_backup(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "demo-project"
            manager = ProjectManager()

            project = manager.create_project(root, "Demo")
            self.assertEqual(project.name, "Demo")
            self.assertTrue(ProjectSerializer.exists(root))

            project.language = "hi"
            project.set_setting("autosave_interval_seconds", 120)
            project.set_setting("backup_retention", 4)
            manager.mark_modified()
            self.assertTrue(manager.save_current())

            reloaded = manager.reload_current()
            self.assertEqual(reloaded.language, "hi")
            self.assertEqual(reloaded.get_setting("autosave_interval_seconds"), 120)
            self.assertEqual(reloaded.get_setting("backup_retention"), 4)

            reloaded.description = "Recovered description"
            manager.mark_modified()
            recovery = manager.autosave()
            self.assertIsNotNone(recovery)
            self.assertTrue(manager.has_recovery())

            reloaded.description = "Unsaved overwrite"
            recovered = manager.recover()
            self.assertEqual(recovered.description, "Recovered description")
            self.assertTrue(manager.modified)

            manager.save_current()
            backup = manager.create_backup()
            self.assertTrue(backup.exists())
            self.assertIn(backup, manager.list_backups())

            manager.project.description = "Changed after backup"
            manager.save_current()
            restored = manager.restore_backup(backup)
            self.assertEqual(restored.description, "Recovered description")

            self.assertTrue(manager.clear_recovery())
            self.assertFalse(manager.has_recovery())
            self.assertTrue(manager.close_current(force=True))
            self.assertFalse(manager.has_project())


if __name__ == "__main__":
    unittest.main()
