from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.project.manager import ProjectManager
from backend.project.serializer import ProjectSerializer


class ProjectLifecycleRegressionTests(unittest.TestCase):
    def test_create_save_reload_recovery_backup_and_close(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            manager = ProjectManager()
            project = manager.create_project(root, "Demo")
            self.assertTrue(ProjectSerializer.exists(root))
            self.assertEqual(manager.current, project)

            project.language = "hi"
            manager.mark_modified()
            self.assertTrue(manager.save_current())
            self.assertFalse(manager.modified)
            self.assertEqual(manager.reload_current().language, "hi")

            manager.project.description = "recovered"
            manager.mark_modified()
            recovery = manager.autosave()
            self.assertTrue(recovery.is_file())
            manager.project.description = "overwritten"
            self.assertEqual(manager.recover().description, "recovered")
            self.assertTrue(manager.modified)

            manager.save_current()
            backup = manager.create_backup()
            self.assertTrue(backup.is_file())
            self.assertIn(backup, manager.list_backups())

            self.assertTrue(manager.clear_recovery())
            self.assertTrue(manager.close_current(force=True))
            self.assertFalse(manager.has_project())

    def test_dirty_close_requires_force_and_shutdown_autosaves(self):
        with tempfile.TemporaryDirectory() as temp:
            manager = ProjectManager()
            manager.create_project(Path(temp) / "project", "Demo")
            manager.mark_modified()
            with self.assertRaises(RuntimeError):
                manager.close_current()
            root = manager.root
            self.assertTrue(manager.shutdown())
            self.assertTrue((root / ".autosave" / "project.json").is_file())
            self.assertFalse(manager.has_project())


if __name__ == "__main__":
    unittest.main()
