from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from backend.project.project import Project
from backend.publishing import ReleaseCalendarService, ReleaseManager


class ReleaseCalendarTests(unittest.TestCase):
    def _seed(self, root: Path, count: int = 3) -> Project:
        episodes = []
        for number in range(1, count + 1):
            episode_id = f"episode_{number:03d}"
            episode_dir = root / "segments" / episode_id
            publish_dir = episode_dir / "publish"
            export_dir = episode_dir / "export"
            publish_dir.mkdir(parents=True, exist_ok=True)
            export_dir.mkdir(parents=True, exist_ok=True)
            (episode_dir / "script.txt").write_text(f"एपिसोड {number}", encoding="utf-8")
            (export_dir / "youtube.mp4").write_bytes(b"video")
            (export_dir / "thumbnail.png").write_bytes(b"png")
            manifest = {
                "episode_id": episode_id,
                "files": {
                    "video": f"segments/{episode_id}/export/youtube.mp4",
                    "thumbnail": f"segments/{episode_id}/export/thumbnail.png",
                },
            }
            (publish_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            episodes.append({
                "episode_id": episode_id,
                "episode_number": number,
                "title": f"भाग {number}",
                "text_file": f"segments/{episode_id}/script.txt",
                "approved": True,
                "status": "approved",
            })
        (root / "segments" / "episodes.json").write_text(
            json.dumps({"episodes": episodes}, ensure_ascii=False), encoding="utf-8"
        )
        manager = ReleaseManager(root)
        for episode in episodes:
            manager.mark_ready(episode["episode_id"])
        return Project(name="Hindi Book", root=root)

    def test_preview_is_non_destructive_and_preserves_episode_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = self._seed(root)
            service = ReleaseCalendarService(project)
            rows = service.preview({
                "timezone": "Asia/Kolkata",
                "start_date": "2026-08-10",
                "local_time": "18:00",
                "interval_days": 2,
                "weekdays": [],
                "playlist_id": "PL_BOOK",
                "ready_only": True,
            })
            self.assertEqual([r["episode_id"] for r in rows], ["episode_001", "episode_002", "episode_003"])
            self.assertEqual([r["local_publish_at"][:10] for r in rows], ["2026-08-10", "2026-08-12", "2026-08-14"])
            self.assertEqual(rows[0]["scheduled_publish_at"], "2026-08-10T12:30:00Z")
            self.assertEqual(ReleaseManager(root).get("episode_001")["scheduled_publish_at"], "")

    def test_weekday_calendar_skips_non_selected_days(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = self._seed(root)
            rows = ReleaseCalendarService(project).preview({
                "timezone": "Asia/Kolkata",
                "start_date": "2026-08-08",
                "local_time": "09:00",
                "interval_days": 1,
                "weekdays": [0, 2, 4],
                "playlist_id": "PL_BOOK",
                "ready_only": True,
            })
            self.assertEqual([r["local_publish_at"][:10] for r in rows], ["2026-08-10", "2026-08-12", "2026-08-14"])

    def test_apply_persists_schedule_playlist_and_preset(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = self._seed(root, count=2)
            service = ReleaseCalendarService(project)
            rows = service.apply({
                "name": "Hindi Daily",
                "timezone": "Asia/Kolkata",
                "start_date": "2026-08-10",
                "local_time": "18:30",
                "interval_days": 1,
                "weekdays": [],
                "playlist_id": "PL_HINDI_BOOK",
                "ready_only": True,
            })
            self.assertEqual(len(rows), 2)
            manager = ReleaseManager(root)
            first = manager.get("episode_001")
            second = manager.get("episode_002")
            self.assertEqual(first["scheduled_publish_at"], "2026-08-10T13:00:00Z")
            self.assertEqual(second["scheduled_publish_at"], "2026-08-11T13:00:00Z")
            self.assertEqual(first["playlist_id"], "PL_HINDI_BOOK")
            self.assertEqual(project.get_setting("release_calendar_preset")["name"], "Hindi Daily")
            self.assertEqual(project.get_setting("publishing_playlist_id"), "PL_HINDI_BOOK")

    def test_ready_only_ignores_draft_episode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = self._seed(root, count=2)
            ReleaseManager(root).mark_draft("episode_001")
            rows = ReleaseCalendarService(project).preview({
                "timezone": "UTC",
                "start_date": "2026-08-10",
                "local_time": "12:00",
                "interval_days": 1,
                "weekdays": [],
                "playlist_id": "",
                "ready_only": True,
            })
            self.assertEqual([r["episode_id"] for r in rows], ["episode_002"])


if __name__ == "__main__":
    unittest.main()
