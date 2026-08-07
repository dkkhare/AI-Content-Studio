from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile


class FFmpegRenderer:
    """Render a slideshow MP4 with progress, cancellation and thumbnail output."""

    def __init__(
        self,
        ffmpeg_path: str | None = None,
        fps: int = 30,
        seconds_per_image: float = 3.0,
        output_name: str = "video.mp4",
        thumbnail_name: str = "thumbnail.jpg",
    ):
        self.ffmpeg_path = ffmpeg_path or shutil.which("ffmpeg") or "ffmpeg"
        self.fps = max(1, int(fps))
        self.seconds_per_image = max(0.1, float(seconds_per_image))
        self.output_name = output_name
        self.thumbnail_name = thumbnail_name

    def available(self) -> bool:
        if Path(self.ffmpeg_path).exists():
            return True
        return shutil.which(self.ffmpeg_path) is not None

    @staticmethod
    def _quote_concat_path(path: Path) -> str:
        return str(path.resolve()).replace("'", "'\\''")

    @staticmethod
    def _progress_seconds(line: str) -> float | None:
        key, separator, value = line.partition("=")
        if not separator:
            return None
        try:
            if key in {"out_time_us", "out_time_ms"}:
                return max(0.0, float(value) / 1_000_000.0)
            if key == "out_time":
                hours, minutes, seconds = value.split(":")
                return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        except (TypeError, ValueError):
            return None
        return None

    def render(self, context, progress=None):
        if not self.available():
            raise RuntimeError(
                "FFmpeg was not found. Install FFmpeg or configure an explicit ffmpeg path."
            )

        images = context.get("video_images") or context.get("ocr_images") or []
        if isinstance(images, (str, Path)):
            images = [images]
        image_paths = [Path(item).resolve() for item in images]
        image_paths = [path for path in image_paths if path.exists() and path.is_file()]
        if not image_paths:
            raise ValueError("Video renderer requires image paths in video_images or ocr_images.")

        if progress:
            progress(5, "Preparing FFmpeg render")

        output_dir = context.project.output_path()
        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / self.output_name
        partial = output.with_name(f"{output.stem}.part{output.suffix}")
        partial.unlink(missing_ok=True)
        expected_duration = max(
            self.seconds_per_image,
            len(image_paths) * self.seconds_per_image,
        )

        with NamedTemporaryFile(
            mode="w",
            suffix=".txt",
            prefix="ai-content-studio-",
            encoding="utf-8",
            delete=False,
        ) as handle:
            list_file = Path(handle.name)
            for image in image_paths:
                quoted = self._quote_concat_path(image)
                handle.write(f"file '{quoted}'\n")
                handle.write(f"duration {self.seconds_per_image}\n")
            handle.write(f"file '{self._quote_concat_path(image_paths[-1])}'\n")

        process: subprocess.Popen | None = None
        succeeded = False
        try:
            command = [
                self.ffmpeg_path,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_file),
            ]

            audio = Path(context.audio_file).resolve() if context.audio_file else None
            if audio is not None and audio.exists():
                command.extend(["-i", str(audio)])

            command.extend(
                [
                    "-vf",
                    f"fps={self.fps},format=yuv420p",
                    "-c:v",
                    "libx264",
                    "-movflags",
                    "+faststart",
                ]
            )

            if audio is not None and audio.exists():
                command.extend(["-c:a", "aac", "-shortest"])

            command.extend(["-progress", "pipe:1", "-nostats", str(partial)])

            if progress:
                progress(10, "Rendering video with FFmpeg")

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            assert process.stdout is not None
            try:
                for raw_line in process.stdout:
                    line = raw_line.strip()
                    seconds = self._progress_seconds(line)
                    if seconds is not None and progress:
                        fraction = min(1.0, seconds / expected_duration)
                        percent = 10 + int(fraction * 80)
                        progress(percent, f"Rendering video: {int(fraction * 100)}%")
            except BaseException:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=3)
                raise

            return_code = process.wait()
            stderr = process.stderr.read().strip() if process.stderr is not None else ""
            if return_code != 0:
                raise RuntimeError(
                    f"FFmpeg render failed: {stderr or 'Unknown FFmpeg error'}"
                )
            if not partial.exists():
                raise RuntimeError("FFmpeg completed without creating the output file.")

            partial.replace(output)
            succeeded = True

            if progress:
                progress(92, "Generating video thumbnail")
            thumbnail = self._generate_thumbnail(output, output_dir)
            if thumbnail is not None:
                try:
                    context.project.thumbnail = str(
                        thumbnail.relative_to(context.project_root)
                    )
                except ValueError:
                    context.project.thumbnail = str(thumbnail)
                context.set("video_thumbnail", str(thumbnail))

            if progress:
                progress(100, "Video rendered")
            return str(output)
        finally:
            try:
                list_file.unlink(missing_ok=True)
            except Exception:
                pass
            if not succeeded:
                try:
                    partial.unlink(missing_ok=True)
                except Exception:
                    pass

    def _generate_thumbnail(self, video: Path, output_dir: Path) -> Path | None:
        thumbnail = output_dir / self.thumbnail_name
        command = [
            self.ffmpeg_path,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            "0",
            "-i",
            str(video),
            "-frames:v",
            "1",
            "-vf",
            "scale=640:-2",
            str(thumbnail),
        ]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0 or not thumbnail.exists():
            return None
        return thumbnail
