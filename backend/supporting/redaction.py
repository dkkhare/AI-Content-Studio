from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from pathlib import Path


REDACTED = "[REDACTED]"
SENSITIVE_KEY = re.compile(
    r"(?:api[_-]?key|authorization|cookie|credential|password|secret|token)",
    re.IGNORECASE,
)
TEXT_PATTERNS = (
    re.compile(r"(?i)(authorization\s*:\s*(?:bearer|basic)\s+)[^\s,;]+"),
    re.compile(
        r"(?i)((?:api[_-]?key|password|secret|token)\s*[=:]\s*)"
        r"([^\s,;]+)"
    ),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
)


def redact_text(value, *, home=None):
    text = str(value)
    for pattern in TEXT_PATTERNS:
        if pattern.groups:
            text = pattern.sub(lambda match: match.group(1) + REDACTED, text)
        else:
            text = pattern.sub(REDACTED, text)
    home_path = str(Path.home().resolve() if home is None else Path(home).resolve())
    if home_path and home_path not in {".", "/"}:
        text = text.replace(home_path, "%USER_HOME%")
        text = text.replace(home_path.replace("\\", "/"), "%USER_HOME%")
    return text


def redact(value, *, home=None, depth=0, max_depth=8, max_items=1000):
    if depth > max_depth:
        return "[TRUNCATED]"
    if isinstance(value, Mapping):
        output = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= max_items:
                output["__truncated__"] = True
                break
            name = str(key)
            output[name] = (
                REDACTED
                if SENSITIVE_KEY.search(name)
                else redact(
                    item,
                    home=home,
                    depth=depth + 1,
                    max_depth=max_depth,
                    max_items=max_items,
                )
            )
        return output
    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        return [
            redact(
                item,
                home=home,
                depth=depth + 1,
                max_depth=max_depth,
                max_items=max_items,
            )
            for item in list(value)[:max_items]
        ]
    if isinstance(value, str):
        return redact_text(value, home=home)
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return redact_text(value, home=home)
