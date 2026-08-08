from __future__ import annotations

import json
import os
import platform
import sys
import threading
import traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from backend.runtime import app_data_dir
from backend.version import VERSION

from .redaction import redact_text


DEFAULT_MAX_REPORTS = 10
DEFAULT_MAX_REPORT_BYTES = 1024 * 1024


class CrashReporter:
    def __init__(
        self,
        directory=None,
        *,
        max_reports=DEFAULT_MAX_REPORTS,
        max_report_bytes=DEFAULT_MAX_REPORT_BYTES,
    ):
        self.directory = Path(
            directory or (app_data_dir() / "crashes")
        ).expanduser().resolve()
        self.max_reports = max(1, int(max_reports))
        self.max_report_bytes = max(1024, int(max_report_bytes))

    def capture(self, exc_type, exc_value, exc_traceback, *, thread="main"):
        if issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
            return None
        self.directory.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc)
        payload = {
            "format": 1,
            "timestamp": now.isoformat(),
            "application_version": VERSION,
            "platform": platform.platform(),
            "python": platform.python_version(),
            "thread": redact_text(thread),
            "exception_type": exc_type.__name__,
            "message": redact_text(str(exc_value)),
            "traceback": redact_text(
                "".join(
                    traceback.format_exception(
                        exc_type,
                        exc_value,
                        exc_traceback,
                    )
                )
            ),
            "upload": "never automatic",
        }
        data = (
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n"
        ).encode("utf-8")
        if len(data) > self.max_report_bytes:
            payload["traceback"] = payload["traceback"][
                : max(0, self.max_report_bytes // 2)
            ] + "\n[TRUNCATED]"
            data = (
                json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
                + "\n"
            ).encode("utf-8")
        if len(data) > self.max_report_bytes:
            raise ValueError("Crash report exceeded the configured size limit.")

        stamp = now.strftime("%Y%m%dT%H%M%S.%fZ")
        destination = self.directory / f"crash-{stamp}-{uuid4().hex[:8]}.json"
        temporary = destination.with_suffix(".json.tmp")
        try:
            with temporary.open("xb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, destination)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        self.prune()
        return destination

    def reports(self):
        if not self.directory.is_dir():
            return ()
        return tuple(
            sorted(
                self.directory.glob("crash-*.json"),
                key=lambda path: (path.stat().st_mtime_ns, path.name),
                reverse=True,
            )
        )

    def prune(self):
        reports = self.reports()
        for path in reports[self.max_reports :]:
            path.unlink(missing_ok=True)


def install_crash_hooks(reporter=None):
    reporter = reporter or CrashReporter()
    previous_main = sys.excepthook
    previous_thread = threading.excepthook

    def main_hook(exc_type, exc_value, exc_traceback):
        try:
            reporter.capture(exc_type, exc_value, exc_traceback, thread="main")
        except Exception:
            pass
        previous_main(exc_type, exc_value, exc_traceback)

    def thread_hook(args):
        try:
            reporter.capture(
                args.exc_type,
                args.exc_value,
                args.exc_traceback,
                thread=getattr(args.thread, "name", "worker"),
            )
        except Exception:
            pass
        previous_thread(args)

    sys.excepthook = main_hook
    threading.excepthook = thread_hook

    def restore():
        if sys.excepthook is main_hook:
            sys.excepthook = previous_main
        if threading.excepthook is thread_hook:
            threading.excepthook = previous_thread

    return reporter, restore
