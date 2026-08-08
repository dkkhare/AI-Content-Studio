from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from threading import Event

from .core import CompositionManifest


class FFmpegRenderError(RuntimeError):
    pass


class RenderCancelled(FFmpegRenderError):
    pass


@dataclass(frozen=True)
class FFmpegStatus:
    available: bool
    executable: str
    version: str = ""
    error: str = ""

    def require(self):
        if not self.available:
            raise FFmpegRenderError(
                self.error
                or "FFmpeg is unavailable. Install FFmpeg and add it to PATH."
            )
        return self


def probe_ffmpeg(executable="ffmpeg", *, runner=subprocess.run, which=shutil.which):
    resolved = which(executable)
    if not resolved and Path(executable).is_file():
        resolved = str(Path(executable).resolve())
    if not resolved:
        return FFmpegStatus(
            False,
            str(executable),
            error="FFmpeg was not found. Install FFmpeg and add it to PATH.",
        )
    try:
        result = runner(
            [resolved, "-version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return FFmpegStatus(False, resolved, error=f"Unable to run FFmpeg: {exc}")
    first_line = (result.stdout or result.stderr or "").splitlines()
    version = first_line[0].strip() if first_line else ""
    if result.returncode != 0 or not version.lower().startswith("ffmpeg version"):
        return FFmpegStatus(
            False,
            resolved,
            version=version,
            error="The configured FFmpeg executable did not return a valid version.",
        )
    return FFmpegStatus(True, resolved, version=version)


def _escape_filter_path(value: str) -> str:
    path = str(value).replace("\\", "/")
    for character in ("\\", ":", "'", ",", "[", "]"):
        path = path.replace(character, "\\" + character)
    return path


class FFmpegCommandBuilder:
    """Translate a composition manifest into a deterministic FFmpeg argv list."""

    def __init__(self, executable: str = "ffmpeg"):
        self.executable = executable

    def build(self, manifest: CompositionManifest, output: str | Path) -> list[str]:
        spec = manifest.spec
        command = [self.executable, "-hide_banner", "-loglevel", "error"]
        if manifest.visual.kind == "image":
            command.extend(["-loop", "1"])
        else:
            command.extend(["-stream_loop", "-1"])
        command.extend(["-i", manifest.visual.path, "-i", manifest.audio.path])

        filters = [
            f"scale={spec.width}:{spec.height}:force_original_aspect_ratio=decrease",
            f"pad={spec.width}:{spec.height}:(ow-iw)/2:(oh-ih)/2",
            f"fps={spec.fps}",
            "format=yuv420p",
        ]
        if manifest.subtitles is not None:
            filters.append(f"subtitles='{_escape_filter_path(manifest.subtitles.path)}'")
        duration = f"{spec.duration_ms / 1000:.3f}"
        command.extend(
            [
                "-vf",
                ",".join(filters),
                "-t",
                duration,
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "20",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-movflags",
                "+faststart",
                "-shortest",
                "-progress",
                "pipe:1",
                "-nostats",
                "-y",
                str(Path(output)),
            ]
        )
        return command


class FFmpegRenderer:
    """Run FFmpeg with progress, cancellation, cleanup, and atomic finalization."""

    def __init__(self, builder=None, popen_factory=None):
        self.builder = builder or FFmpegCommandBuilder()
        self.popen_factory = popen_factory or subprocess.Popen

    def preflight(self):
        return probe_ffmpeg(self.builder.executable)

    @staticmethod
    def progress_from_line(line: str, duration_ms: int) -> float | None:
        key, separator, raw = line.strip().partition("=")
        if not separator or key not in {"out_time_us", "out_time_ms"}:
            return None
        try:
            elapsed_ms = int(raw) / 1000
        except ValueError:
            return None
        return min(100.0, max(0.0, elapsed_ms * 100.0 / duration_ms))

    def render(
        self,
        manifest: CompositionManifest,
        output: str | Path,
        *,
        progress=None,
        cancel_event: Event | None = None,
    ) -> Path:
        target = Path(output).resolve()
        if target.suffix.lower() != ".mp4":
            raise ValueError("Video output must use the .mp4 extension.")
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.stem + ".partial" + target.suffix)
        temporary.unlink(missing_ok=True)
        command = self.builder.build(manifest, temporary)
        process = self.popen_factory(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        diagnostics = []
        try:
            for line in process.stdout or ():
                diagnostics.append(line.rstrip())
                if cancel_event is not None and cancel_event.is_set():
                    process.terminate()
                    process.wait()
                    raise RenderCancelled("Video rendering was cancelled.")
                value = self.progress_from_line(line, manifest.spec.duration_ms)
                if value is not None and progress is not None:
                    progress(value)
            return_code = process.wait()
            if cancel_event is not None and cancel_event.is_set():
                raise RenderCancelled("Video rendering was cancelled.")
            if return_code:
                detail = "\n".join(diagnostics[-20:]).strip()
                raise FFmpegRenderError(
                    f"FFmpeg exited with status {return_code}"
                    + (f":\n{detail}" if detail else ".")
                )
            if not temporary.is_file():
                raise FFmpegRenderError("FFmpeg completed without producing an output file.")
            temporary.replace(target)
            if progress is not None:
                progress(100.0)
            return target
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
