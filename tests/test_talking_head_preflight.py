from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from backend.talking_head.preflight import TalkingHeadPreflight


class Disk:
    free = 30 * 1024 ** 3


class TalkingHeadPreflightTests(unittest.TestCase):
    def _runtime(self, root: Path):
        sad = root / "SadTalker"
        (sad / "checkpoints").mkdir(parents=True)
        (sad / "inference.py").write_text("# inference", encoding="utf-8")
        (sad / "checkpoints" / "model.safetensors").write_bytes(b"model")
        python = root / "python.exe"
        python.write_bytes(b"python")
        return sad, python

    def test_ready_report_checks_all_required_runtimes_without_loading_models(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            sad, python = self._runtime(root)
            calls = []

            def runner(command, **kwargs):
                calls.append(command)
                if "-version" in command:
                    return SimpleNamespace(
                        returncode=0,
                        stdout="ffmpeg version 7.1 test\n",
                        stderr="",
                    )
                if "--query-gpu=memory.total" in command:
                    return SimpleNamespace(returncode=0, stdout="4096\n", stderr="")
                if "sys.version" in command[-1]:
                    return SimpleNamespace(returncode=0, stdout="3.11.9\n", stderr="")
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            preflight = TalkingHeadPreflight(
                runner=runner,
                which=lambda value: str(python) if value == str(python) else (
                    value if value in {"ffmpeg", "nvidia-smi"} else None
                ),
                find_spec=lambda value: object() if value == "f5_tts" else None,
                disk_usage=lambda value: Disk(),
            )
            report = preflight.run(
                sadtalker_directory=sad,
                sadtalker_python=str(python),
                output_directory=root / "output",
            )
            self.assertTrue(report.ready)
            self.assertFalse(report.failures)
            self.assertIn("[PASS]", "\n".join(report.lines()))
            self.assertFalse(any("import f5_tts" in " ".join(call) for call in calls))

    def test_missing_models_f5_ffmpeg_and_python_are_blocking(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            sad = root / "SadTalker"
            sad.mkdir()
            (sad / "inference.py").write_text("# inference", encoding="utf-8")
            report = TalkingHeadPreflight(
                which=lambda value: None,
                find_spec=lambda value: None,
                disk_usage=lambda value: Disk(),
            ).run(
                sadtalker_directory=sad,
                sadtalker_python="missing-python",
                output_directory=root / "output",
            )
            self.assertFalse(report.ready)
            keys = {item.key for item in report.failures}
            self.assertTrue(
                {"sadtalker-models", "sadtalker-python", "f5-tts", "ffmpeg"}
                <= keys
            )

    def test_low_disk_and_undetected_gpu_are_warnings_not_false_blockers(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            sad, python = self._runtime(root)

            def runner(command, **kwargs):
                if "-version" in command:
                    return SimpleNamespace(
                        returncode=0, stdout="ffmpeg version 7.1\n", stderr=""
                    )
                if "sys.version" in command[-1]:
                    return SimpleNamespace(returncode=0, stdout="3.11\n", stderr="")
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            class LowDisk:
                free = 2 * 1024 ** 3

            report = TalkingHeadPreflight(
                runner=runner,
                which=lambda value: str(python) if value == str(python) else (
                    "ffmpeg" if value == "ffmpeg" else None
                ),
                find_spec=lambda value: object(),
                disk_usage=lambda value: LowDisk(),
            ).run(
                sadtalker_directory=sad,
                sadtalker_python=str(python),
                output_directory=root / "output",
            )
            self.assertTrue(report.ready)
            self.assertEqual(
                {item.key for item in report.warnings},
                {"disk-space", "gpu-memory"},
            )


if __name__ == "__main__":
    unittest.main()
