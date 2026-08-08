from __future__ import annotations

import importlib.util
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from backend.video.ffmpeg import probe_ffmpeg


@dataclass(frozen=True, slots=True)
class PreflightCheck:
    key: str
    ok: bool
    required: bool
    message: str
    remediation: str = ""


@dataclass(frozen=True, slots=True)
class PreflightReport:
    checks: tuple[PreflightCheck, ...]

    @property
    def ready(self) -> bool:
        return all(item.ok for item in self.checks if item.required)

    @property
    def failures(self) -> tuple[PreflightCheck, ...]:
        return tuple(item for item in self.checks if item.required and not item.ok)

    @property
    def warnings(self) -> tuple[PreflightCheck, ...]:
        return tuple(item for item in self.checks if not item.required and not item.ok)

    def lines(self) -> list[str]:
        values = []
        for item in self.checks:
            status = "PASS" if item.ok else ("FAIL" if item.required else "WARN")
            value = f"[{status}] {item.message}"
            if not item.ok and item.remediation:
                value += f" — {item.remediation}"
            values.append(value)
        return values


class TalkingHeadPreflight:
    """Fast checks that do not load either heavyweight model."""

    REQUIRED_SADTALKER_MODULES = (
        "torch",
        "numpy",
        "cv2",
        "scipy",
        "skimage",
        "yaml",
        "safetensors",
    )

    def __init__(
        self,
        *,
        runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
        which: Callable[[str], str | None] = shutil.which,
        find_spec=importlib.util.find_spec,
        disk_usage=shutil.disk_usage,
    ):
        self.runner = runner
        self.which = which
        self.find_spec = find_spec
        self.disk_usage = disk_usage

    def _python(self, executable: str) -> tuple[PreflightCheck, PreflightCheck]:
        path = self.which(executable)
        if not path and Path(executable).is_file():
            path = str(Path(executable).resolve())
        if not path:
            missing = PreflightCheck(
                "sadtalker-python",
                False,
                True,
                "SadTalker Python executable was not found.",
                "Select python.exe from the dedicated SadTalker environment.",
            )
            return missing, PreflightCheck(
                "sadtalker-packages", False, True,
                "SadTalker package check could not run.", missing.remediation
            )
        version = self.runner(
            [path, "-c", "import sys; print(sys.version.split()[0])"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=15, check=False,
        )
        python_ok = version.returncode == 0
        python_check = PreflightCheck(
            "sadtalker-python",
            python_ok,
            True,
            (
                f"SadTalker Python is available ({version.stdout.strip()})."
                if python_ok
                else "SadTalker Python could not start."
            ),
            "Repair or recreate the dedicated SadTalker environment.",
        )
        script = (
            "import importlib.util;"
            f"mods={self.REQUIRED_SADTALKER_MODULES!r};"
            "missing=[m for m in mods if importlib.util.find_spec(m) is None];"
            "print(','.join(missing));"
            "raise SystemExit(bool(missing))"
        )
        packages = self.runner(
            [path, "-c", script],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=30, check=False,
        )
        missing_names = packages.stdout.strip()
        package_ok = packages.returncode == 0
        package_check = PreflightCheck(
            "sadtalker-packages",
            package_ok,
            True,
            (
                "SadTalker Python dependencies are available."
                if package_ok
                else f"SadTalker dependencies are missing: {missing_names or 'unknown'}."
            ),
            "Activate the SadTalker environment and install its requirements.",
        )
        return python_check, package_check

    def _gpu(self, size: int, enhancer: str) -> PreflightCheck:
        executable = self.which("nvidia-smi")
        if not executable:
            return PreflightCheck(
                "gpu-memory", False, False,
                "NVIDIA VRAM could not be detected; CPU generation may be very slow.",
                "Install a current NVIDIA driver or continue with CPU fallback.",
            )
        result = self.runner(
            [
                executable,
                "--query-gpu=memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=10, check=False,
        )
        try:
            memory = min(
                int(line.strip()) for line in result.stdout.splitlines() if line.strip()
            )
        except (ValueError, TypeError):
            memory = 0
        recommended = 8192 if size == 512 or enhancer else 4096
        ok = memory >= recommended
        return PreflightCheck(
            "gpu-memory",
            ok,
            False,
            (
                f"Detected {memory} MB VRAM; configuration target is {recommended} MB."
                if memory
                else "NVIDIA VRAM query returned no usable value."
            ),
            (
                "Use size 256, crop mode, no enhancer, and 30–45 second segments."
            ),
        )

    def run(
        self,
        *,
        sadtalker_directory: str | Path,
        sadtalker_python: str,
        output_directory: str | Path,
        ffmpeg: str = "ffmpeg",
        size: int = 256,
        enhancer: str = "",
    ) -> PreflightReport:
        root = Path(sadtalker_directory)
        inference = root / "inference.py"
        checkpoints = root / "checkpoints"
        model_files = (
            list(checkpoints.glob("*.safetensors"))
            + list(checkpoints.glob("*.pth"))
            + list(checkpoints.glob("*.pth.tar"))
            if checkpoints.is_dir()
            else []
        )
        checks: list[PreflightCheck] = [
            PreflightCheck(
                "sadtalker-repository",
                inference.is_file(),
                True,
                (
                    "SadTalker inference.py is available."
                    if inference.is_file()
                    else "SadTalker inference.py was not found."
                ),
                "Select the root of an installed SadTalker checkout.",
            ),
            PreflightCheck(
                "sadtalker-models",
                bool(model_files),
                True,
                (
                    f"SadTalker checkpoints found ({len(model_files)} files)."
                    if model_files
                    else "SadTalker checkpoints were not found."
                ),
                "Download official SadTalker checkpoints into its checkpoints folder.",
            ),
        ]
        checks.extend(self._python(sadtalker_python))
        f5_available = self.find_spec("f5_tts") is not None
        checks.append(
            PreflightCheck(
                "f5-tts",
                f5_available,
                True,
                (
                    "F5-TTS is available in the AI Content Studio environment."
                    if f5_available
                    else "F5-TTS is not installed in the application environment."
                ),
                "Run in source mode and install requirements-tts.txt.",
            )
        )
        ffmpeg_status = probe_ffmpeg(ffmpeg, runner=self.runner, which=self.which)
        checks.append(
            PreflightCheck(
                "ffmpeg",
                ffmpeg_status.available,
                True,
                (
                    ffmpeg_status.version
                    if ffmpeg_status.available
                    else ffmpeg_status.error
                ),
                "Install FFmpeg and add its bin directory to PATH.",
            )
        )
        output = Path(output_directory)
        writable = False
        try:
            output.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=output, delete=True):
                writable = True
        except OSError:
            pass
        checks.append(
            PreflightCheck(
                "output-writable",
                writable,
                True,
                (
                    f"Output directory is writable: {output}"
                    if writable
                    else f"Output directory is not writable: {output}"
                ),
                "Choose a writable folder inside the current project.",
            )
        )
        try:
            free_gb = self.disk_usage(output).free / (1024 ** 3)
        except OSError:
            free_gb = 0.0
        checks.append(
            PreflightCheck(
                "disk-space",
                free_gb >= 20.0,
                False,
                f"Output drive has {free_gb:.1f} GB free.",
                "Free at least 20 GB; complete books may require much more.",
            )
        )
        checks.append(self._gpu(size, enhancer))
        return PreflightReport(tuple(checks))
