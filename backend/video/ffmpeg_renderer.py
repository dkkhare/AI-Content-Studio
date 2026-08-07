from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile


class FFmpegRenderer:
    """Render a simple slideshow MP4 from project images and narration audio."""

    def __init__(
        self,
        ffmpeg_path: str | None = None,
        fps: int = 30,
        seconds_per_image: float = 3.0,
        output_name: str = "video.mp4",
    ):
        self.ffmpeg_path = ffmpeg_path or shutil.which("ffmpeg") or "ffmpeg"
        self.fps = max(1, int(fps))
        self.seconds_per_image = max(0.1, float(seconds_per_image))
        self.output_name = output_name

    def available(self) -> bool:
        if Path(self.ffmpeg_path).exists():
            return True
        return shutil.which(self.ffmpeg_path) is not None

    @staticmethod
    def _quote_concat_path(path: Path) -> str:
        return str(path.resolve()).replace("'", "'\\''")

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
            progress(10, "Preparing FFmpeg render")

        output_dir = context.project.output_path()
        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / self.output_name

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
            # concat demuxer needs the final item repeated for its duration.
            handle.write(f"file '{self._quote_concat_path(image_paths[-1])}'\n")

        try:
            command = [
                self.ffmpeg_path,
                "-y",
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

            command.append(str(output))

            if progress:
                progress(30, "Rendering video with FFmpeg")

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                message = result.stderr.strip() or result.stdout.strip() or "Unknown FFmpeg error"
                raise RuntimeError(f"FFmpeg render failed: {message}")

            if not output.exists():
                raise RuntimeError("FFmpeg completed without creating the output file.")

            if progress:
                progress(100, "Video rendered")
            return str(output)
        finally:
            try:
                list_file.unlink(missing_ok=True)
            except Exception:
                pass
