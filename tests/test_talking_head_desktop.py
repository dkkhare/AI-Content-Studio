from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from backend.project.project import Project
from backend.talking_head import BookImportResult, SourceBlock
from desktop.controllers.talking_head_controller import TalkingHeadController


class Importer:
    def import_book(self, path):
        return BookImportResult(
            str(path),
            "txt",
            (
                SourceBlock("one", "Chapter One", "word " * 900 + "."),
                SourceBlock("two", "Chapter Two", "word " * 900 + "."),
            ),
        )


class TalkingHeadDesktopTests(unittest.TestCase):
    def test_preview_returns_complete_ordered_episode_plan(self):
        controller = TalkingHeadController(importer=Importer())
        imported, plan = controller.preview(
            "book.txt", episode_minutes=5, words_per_minute=120
        )
        self.assertEqual([item.block_id for item in imported.blocks], ["one", "two"])
        plan.validate_coverage()
        self.assertEqual(plan.source_order, ("one", "two"))

    def test_project_context_uses_recoverable_project_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            project = Project("Series", Path(folder)).initialize()
            context = TalkingHeadController(importer=Importer()).set_project(project)
            self.assertEqual(
                Path(context["output_directory"]),
                Path(folder).resolve() / "output" / "talking-head-series",
            )
            self.assertEqual(
                Path(context["work_directory"]),
                Path(folder).resolve() / "output" / ".talking-head-work",
            )

    def test_output_escape_is_rejected_before_worker_starts(self):
        with tempfile.TemporaryDirectory() as folder, tempfile.TemporaryDirectory() as outside:
            project = Project("Series", Path(folder)).initialize()
            controller = TalkingHeadController(importer=Importer())
            controller.set_project(project)
            with self.assertRaisesRegex(ValueError, "inside the project"):
                controller.start(
                    output_directory=outside,
                    work_directory=Path(folder) / "output" / ".work",
                )
            self.assertFalse(controller.is_running())

    def test_project_model_persists_series_manifest_asset(self):
        with tempfile.TemporaryDirectory() as folder:
            project = Project("Series", Path(folder)).initialize()
            manifest = Path(folder) / "output" / "talking-head-series" / "series.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text("{}", encoding="utf-8")
            project.register_asset("talking_head_series_manifest", str(manifest))
            self.assertEqual(
                project.get_output_files()["talking_head_series_manifest"],
                str(manifest),
            )
            restored = Project.from_dict(project.to_dict())
            self.assertEqual(restored.talking_head_series_manifest, str(manifest))


if __name__ == "__main__":
    unittest.main()
