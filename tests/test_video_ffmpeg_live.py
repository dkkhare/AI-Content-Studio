from __future__ import annotations

import binascii
import json
import os
import struct
import subprocess
import tempfile
import unittest
import wave
import zlib
from pathlib import Path

from backend.video import FFmpegRenderer, VideoComposer


def write_png(path, width=32, height=24):
    def chunk(kind, data):
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
        )

    row = b"\x00" + b"\x20\x60\xc0" * width
    raw = row * height
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def write_wav(path, seconds=0.6, rate=8000):
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(rate)
        audio.writeframes(b"\x00\x00" * round(seconds * rate))


@unittest.skipUnless(
    os.environ.get("AI_STUDIO_RUN_FFMPEG_SMOKE") == "1",
    "live FFmpeg smoke is opt-in",
)
class LiveFFmpegSmokeTests(unittest.TestCase):
    def test_real_render_and_ffprobe_metadata(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            image = root / "cover.png"
            audio = root / "audio.wav"
            output = root / "video.mp4"
            write_png(image)
            write_wav(audio)

            manifest = VideoComposer().plan(
                visual=image,
                audio=audio,
                duration_seconds=0.6,
                width=160,
                height=120,
                fps=10,
            )
            renderer = FFmpegRenderer()
            renderer.preflight().require()
            progress = []
            result = renderer.render(manifest, output, progress=progress.append)

            self.assertEqual(result, output.resolve())
            self.assertGreater(output.stat().st_size, 0)
            self.assertEqual(progress[-1], 100.0)
            self.assertFalse((root / "video.partial.mp4").exists())

            probe = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "stream=codec_type,codec_name,width,height",
                    "-of",
                    "json",
                    str(output),
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            streams = json.loads(probe.stdout)["streams"]
            video = next(item for item in streams if item["codec_type"] == "video")
            sound = next(item for item in streams if item["codec_type"] == "audio")
            self.assertEqual(video["codec_name"], "h264")
            self.assertEqual((video["width"], video["height"]), (160, 120))
            self.assertEqual(sound["codec_name"], "aac")


if __name__ == "__main__":
    unittest.main()
