from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.episodes import EpisodeReviewStore, SegmentPlanner
from backend.pipeline.context import PipelineContext
from backend.pipeline.episode_stage import EpisodeNarrationStage
from backend.project.project import Project


class FakeNarrationPipeline:
    calls: list[tuple[str, str]] = []

    def generate(self, job):
        self.calls.append((job.text, job.reference_voice))
        output = Path(job.output_folder) / "narration.wav"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"RIFFfake")
        return str(output)


class EpisodeNarrationTests(unittest.TestCase):
    def _prepare(self, root: Path):
        project = Project("Hindi", root).initialize()
        voice = root / "voice.wav"
        voice.write_bytes(b"RIFFvoice")
        project.voice = str(voice)

        planner = SegmentPlanner(
            target_minutes=1,
            min_minutes=1,
            max_minutes=2,
            words_per_minute=20,
        )
        text = "अध्याय 1\n\n" + "शब्द " * 25 + "।\n\nअध्याय 2\n\n" + "वाक्य " * 25 + "।"
        planner.persist(root, planner.plan(text))
        return project, EpisodeReviewStore(root)

    def test_pending_review_blocks_episode_narration(self):
        with tempfile.TemporaryDirectory() as temp:
            project, _ = self._prepare(Path(temp))
            context = PipelineContext(project)
            stage = EpisodeNarrationStage(pipeline_factory=FakeNarrationPipeline)
            with self.assertRaisesRegex(ValueError, "review is incomplete"):
                stage.execute(context)

    def test_only_approved_episodes_generate_audio(self):
        with tempfile.TemporaryDirectory() as temp:
            project, store = self._prepare(Path(temp))
            episodes = store.episodes()
            self.assertGreaterEqual(len(episodes), 1)
            for index, episode in enumerate(episodes):
                episode_id = str(episode["episode_id"])
                if index == 0:
                    store.approve(episode_id)
                else:
                    store.skip(episode_id)

            FakeNarrationPipeline.calls = []
            context = PipelineContext(project)
            stage = EpisodeNarrationStage(pipeline_factory=FakeNarrationPipeline)
            outputs = stage.execute(context)

            self.assertEqual(len(outputs), 1)
            self.assertEqual(outputs[0]["episode_id"], str(episodes[0]["episode_id"]))
            self.assertTrue(Path(outputs[0]["audio_file"]).exists())
            self.assertEqual(len(FakeNarrationPipeline.calls), 1)
            self.assertEqual(FakeNarrationPipeline.calls[0][1], project.voice)
            self.assertEqual(context.get("episode_audio_files"), outputs)


if __name__ == "__main__":
    unittest.main()
