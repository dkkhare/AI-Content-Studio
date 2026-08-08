from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from backend.talking_head import (
    SeriesRequest,
    SourceBlock,
    TalkingHeadSeriesPipeline,
)


def chapter(word_count: int) -> str:
    return " ".join(f"word{i}" for i in range(word_count)) + "."


class TalkingHeadSeriesTests(unittest.TestCase):
    def _request(self, root: Path) -> SeriesRequest:
        portrait = root / "writer.png"
        voice = root / "voice.wav"
        portrait.write_bytes(b"portrait")
        voice.write_bytes(b"voice")
        return SeriesRequest(
            blocks=(
                SourceBlock("chapter-1", "Beginning", chapter(900)),
                SourceBlock("chapter-2", "Middle", chapter(900)),
                SourceBlock("chapter-3", "Ending", chapter(900)),
            ),
            portrait=portrait,
            reference_audio=voice,
            reference_text="Exact sample transcript.",
            output_directory=root / "series",
            work_directory=root / "work",
            episode_minutes=5,
            words_per_minute=120,
            rights_confirmed=True,
        )

    def test_generates_numbered_episodes_manifest_and_playlist(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            calls = []

            class EpisodePipeline:
                def run(self, request, **kwargs):
                    calls.append(request)
                    request.output.parent.mkdir(parents=True, exist_ok=True)
                    request.output.write_bytes(request.script.encode("utf-8"))
                    return SimpleNamespace(output=str(request.output))

            result = TalkingHeadSeriesPipeline(EpisodePipeline()).run(
                self._request(root)
            )
            self.assertGreater(len(result.episodes), 1)
            self.assertEqual(len(calls), len(result.episodes))
            self.assertTrue(Path(result.manifest).is_file())
            self.assertTrue(Path(result.playlist).is_file())
            self.assertTrue(result.episodes[0].output.startswith("episode-001-"))
            covered = []
            for item in result.episodes:
                for source_id in item.source_ids:
                    if source_id not in covered:
                        covered.append(source_id)
            self.assertEqual(covered, ["chapter-1", "chapter-2", "chapter-3"])

    def test_second_run_resumes_checksum_valid_episodes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)

            class EpisodePipeline:
                calls = 0

                def run(self, request, **kwargs):
                    self.calls += 1
                    request.output.parent.mkdir(parents=True, exist_ok=True)
                    request.output.write_bytes(request.script.encode("utf-8"))
                    return SimpleNamespace(output=str(request.output))

            episode_pipeline = EpisodePipeline()
            pipeline = TalkingHeadSeriesPipeline(episode_pipeline)
            request = self._request(root)
            first = pipeline.run(request)
            second = pipeline.run(request)
            self.assertEqual(episode_pipeline.calls, len(first.episodes))
            self.assertEqual(second.resumed_episodes, len(second.episodes))

    def test_changed_voice_invalidates_previous_series(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)

            class EpisodePipeline:
                calls = 0

                def run(self, request, **kwargs):
                    self.calls += 1
                    request.output.parent.mkdir(parents=True, exist_ok=True)
                    request.output.write_bytes(request.script.encode("utf-8"))
                    return SimpleNamespace(output=str(request.output))

            worker = EpisodePipeline()
            pipeline = TalkingHeadSeriesPipeline(worker)
            request = self._request(root)
            first = pipeline.run(request)
            request.reference_audio.write_bytes(b"changed voice")
            second = pipeline.run(request)
            self.assertEqual(second.resumed_episodes, 0)
            self.assertEqual(worker.calls, len(first.episodes) + len(second.episodes))

    def test_rights_confirmation_is_required(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            request = self._request(root)
            denied = SeriesRequest(
                blocks=request.blocks,
                portrait=request.portrait,
                reference_audio=request.reference_audio,
                reference_text=request.reference_text,
                output_directory=request.output_directory,
                work_directory=request.work_directory,
                episode_minutes=request.episode_minutes,
                words_per_minute=request.words_per_minute,
                rights_confirmed=False,
            )
            with self.assertRaisesRegex(ValueError, "Confirm permission"):
                denied.validate()


if __name__ == "__main__":
    unittest.main()
