from __future__ import annotations

import unittest

from backend.video.ffmpeg_renderer import FFmpegRenderer


class FFmpegRendererTests(unittest.TestCase):
    def test_progress_seconds_from_microseconds(self):
        self.assertEqual(FFmpegRenderer._progress_seconds("out_time_us=2500000"), 2.5)
        self.assertEqual(FFmpegRenderer._progress_seconds("out_time_ms=1000000"), 1.0)

    def test_progress_seconds_from_timestamp(self):
        value = FFmpegRenderer._progress_seconds("out_time=00:01:02.500000")
        self.assertAlmostEqual(value, 62.5)

    def test_unrelated_progress_line_is_ignored(self):
        self.assertIsNone(FFmpegRenderer._progress_seconds("progress=continue"))
        self.assertIsNone(FFmpegRenderer._progress_seconds("invalid"))


if __name__ == "__main__":
    unittest.main()
