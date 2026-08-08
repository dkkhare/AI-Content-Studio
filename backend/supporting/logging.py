from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

from backend.runtime import app_data_dir
from backend.version import VERSION

from .redaction import redact_text


LOGGER_NAME = "ai_content_studio"


class RedactedJsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": datetime.fromtimestamp(
                record.created, timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "message": redact_text(record.getMessage()),
        }
        if record.exc_info:
            payload["exception"] = redact_text(
                self.formatException(record.exc_info)
            )
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def configure_logging(
    directory=None,
    *,
    max_bytes=2 * 1024 * 1024,
    backup_count=5,
    level=logging.INFO,
):
    directory = Path(directory or (app_data_dir() / "logs")).expanduser().resolve()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "application.log"
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False

    for handler in logger.handlers:
        if getattr(handler, "_ai_content_studio_log", False):
            return logger, path

    handler = RotatingFileHandler(
        path,
        maxBytes=max(1, int(max_bytes)),
        backupCount=max(0, int(backup_count)),
        encoding="utf-8",
        delay=True,
    )
    handler._ai_content_studio_log = True
    handler.setFormatter(RedactedJsonFormatter())
    logger.addHandler(handler)
    logger.info("Logging initialized for AI Content Studio %s", VERSION)
    return logger, path
