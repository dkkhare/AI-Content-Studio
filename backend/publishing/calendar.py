from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .release import ReleaseManager


class ReleaseCalendarService:
    """Preview and apply deterministic publishing calendars to ordered Ready episodes."""

    def __init__(self, project):
        self.project = project
        self.releases = ReleaseManager(project.root)

    @staticmethod
    def _parse_weekdays(value: Any) -> list[int]:
        if value in (None, "", []):
            return []
        raw = value if isinstance(value, (list, tuple, set)) else str(value).split(",")
        names = {
            "mon": 0, "monday": 0,
            "tue": 1, "tues": 1, "tuesday": 1,
            "wed": 2, "wednesday": 2,
            "thu": 3, "thur": 3, "thurs": 3, "thursday": 3,
            "fri": 4, "friday": 4,
            "sat": 5, "saturday": 5,
            "sun": 6, "sunday": 6,
        }
        result: list[int] = []
        for item in raw:
            text = str(item).strip().lower()
            if not text:
                continue
            if text in names:
                day = names[text]
            else:
                try:
                    day = int(text)
                except ValueError as exc:
                    raise ValueError(f"Invalid weekday: {item}") from exc
                if not 0 <= day <= 6:
                    raise ValueError("Weekdays must be 0..6 where Monday=0.")
            if day not in result:
                result.append(day)
        return sorted(result)

    @staticmethod
    def _timezone(name: str) -> ZoneInfo:
        value = str(name or "").strip() or "Asia/Kolkata"
        try:
            return ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"Unknown IANA timezone: {value}") from exc

    @staticmethod
    def _local_time(value: str) -> time:
        text = str(value or "").strip() or "18:00"
        try:
            parsed = time.fromisoformat(text)
        except ValueError as exc:
            raise ValueError("Publish time must be HH:MM or HH:MM:SS.") from exc
        return parsed.replace(tzinfo=None)

    @staticmethod
    def _start_date(value: str) -> date:
        text = str(value or "").strip()
        if not text:
            return date.today()
        try:
            return date.fromisoformat(text)
        except ValueError as exc:
            raise ValueError("Start date must be YYYY-MM-DD.") from exc

    def preset(self) -> dict[str, Any]:
        raw = self.project.get_setting("release_calendar_preset", {})
        preset = dict(raw) if isinstance(raw, dict) else {}
        preset.setdefault("name", "Default Release Calendar")
        preset.setdefault("timezone", "Asia/Kolkata")
        preset.setdefault("start_date", date.today().isoformat())
        preset.setdefault("local_time", "18:00")
        preset.setdefault("interval_days", 1)
        preset.setdefault("weekdays", [])
        preset.setdefault("playlist_id", str(self.project.get_setting("publishing_playlist_id", "") or ""))
        preset.setdefault("ready_only", True)
        return preset

    def save_preset(self, preset: dict[str, Any]) -> dict[str, Any]:
        normalized = self._normalize_preset(preset)
        self.project.update_settings({
            "release_calendar_preset": normalized,
            "publishing_playlist_id": normalized["playlist_id"],
        })
        return normalized

    def _normalize_preset(self, preset: dict[str, Any]) -> dict[str, Any]:
        source = dict(preset or {})
        tz = self._timezone(str(source.get("timezone", "Asia/Kolkata")))
        start = self._start_date(str(source.get("start_date", "")))
        local_time = self._local_time(str(source.get("local_time", "18:00")))
        interval = max(1, int(source.get("interval_days", 1) or 1))
        weekdays = self._parse_weekdays(source.get("weekdays", []))
        return {
            "name": str(source.get("name", "Default Release Calendar") or "Default Release Calendar").strip(),
            "timezone": str(tz.key),
            "start_date": start.isoformat(),
            "local_time": local_time.isoformat(timespec="minutes"),
            "interval_days": interval,
            "weekdays": weekdays,
            "playlist_id": str(source.get("playlist_id", "") or "").strip(),
            "ready_only": bool(source.get("ready_only", True)),
        }

    @staticmethod
    def _next_weekday(current: date, weekdays: list[int]) -> date:
        candidate = current
        while candidate.weekday() not in weekdays:
            candidate += timedelta(days=1)
        return candidate

    def preview(self, preset: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        config = self._normalize_preset(preset or self.preset())
        tz = self._timezone(config["timezone"])
        local_clock = self._local_time(config["local_time"])
        current = self._start_date(config["start_date"])
        weekdays = list(config["weekdays"])
        interval = int(config["interval_days"])
        rows = []

        eligible = []
        for release in self.releases.items():
            state = str(release.get("state", "draft"))
            if state == "published":
                continue
            if config["ready_only"] and state != "ready":
                continue
            eligible.append(release)

        for index, release in enumerate(eligible):
            if weekdays:
                current = self._next_weekday(current, weekdays)
            local_dt = datetime.combine(current, local_clock, tzinfo=tz)
            utc_dt = local_dt.astimezone(timezone.utc)
            rows.append({
                "episode_id": str(release.get("episode_id", "")),
                "episode_number": int(release.get("episode_number", 0) or 0),
                "title": str(release.get("title", "")),
                "local_publish_at": local_dt.isoformat(),
                "scheduled_publish_at": utc_dt.isoformat().replace("+00:00", "Z"),
                "timezone": config["timezone"],
                "playlist_id": config["playlist_id"],
            })
            if weekdays:
                current += timedelta(days=1)
            else:
                current += timedelta(days=interval)
        return rows

    def apply(self, preset: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        config = self.save_preset(preset or self.preset())
        rows = self.preview(config)
        for row in rows:
            self.releases.configure_distribution(
                row["episode_id"],
                publish_at=row["scheduled_publish_at"],
                playlist_id=row["playlist_id"],
            )
        return rows
