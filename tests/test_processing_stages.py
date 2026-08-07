from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.pipeline import (
    NarrationStage,
    OCRStage,
    PipelineContext,
    TranslationStage,
    VideoRenderStage,
)
from backend.project.project import Project


class FakeOCRManager:
    def __init__(self):
        self.provider = None

    def set_provider(self, name):
        self.provider = name

    def recognize(self, image):
        return {"text": f"text:{Path(image).stem}"}


class FakeNarrationPipeline:
    def generate(self, job):
        output = Path(job.output_folder) / "narration.wav"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"RIFFfake")
        return str(output)


class ProcessingStageTests(unittest.TestCase):
    def test_ocr_translation_narration_and_video_adapters(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            root.mkdir()
            project = Project(name="Demo", root=root)
            project.initialize()

            images = []
            for number in (1, 2):
                image = root / f"page-{number}.png"
                image.write_bytes(b"fake")
                images.append(str(image))

            reference_voice = root / "hindi-reference.wav"
            reference_voice.write_bytes(b"voice")
            context = PipelineContext(
                project,
                {
                    "ocr_images": images,
                    "reference_voice": str(reference_voice),
                },
            )

            OCRStage(
                provider="fake",
                manager_factory=FakeOCRManager,
            ).execute(context)
            self.assertEqual(context.get("ocr_pages"), ["text:page-1", "text:page-2"])
            self.assertTrue((root / "output" / "ocr.txt").exists())

            TranslationStage(lambda text: text.upper()).execute(context)
            self.assertEqual(
                context.get("translated_pages"),
                ["TEXT:PAGE-1", "TEXT:PAGE-2"],
            )
            self.assertTrue((root / "output" / "translation.txt").exists())

            audio = NarrationStage(
                pipeline_factory=FakeNarrationPipeline,
            ).execute(context)
            self.assertTrue(Path(audio).exists())
            self.assertTrue(project.narration_file)
            self.assertTrue(project.podcast_file)

            def renderer(ctx, progress=None):
                output = ctx.path("output", "video.mp4", create_parent=True)
                output.write_bytes(b"video")
                if progress:
                    progress(50, "rendering")
                return output

            video = VideoRenderStage(renderer).execute(context)
            self.assertTrue(Path(video).exists())
            self.assertTrue(project.video_file)


if __name__ == "__main__":
    unittest.main()
