from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from scripts.release_version import read_version


REQUIRED_GATES = (
    "project_lifecycle",
    "ai_core",
    "safe_updates",
    "support_diagnostics",
    "windows_package",
    "windows_installer",
)
VALID_STATUSES = {"pass", "fail", "pending"}


def parse_gate(value):
    name, separator, status = value.partition("=")
    if not separator or not name or status not in VALID_STATUSES:
        raise argparse.ArgumentTypeError(
            "gate must use NAME=pass, NAME=fail, or NAME=pending"
        )
    if name not in REQUIRED_GATES:
        raise argparse.ArgumentTypeError(f"unknown release gate: {name}")
    return name, status


def build_evidence(*, commit, version, gates, generated_at=None):
    statuses = {name: "pending" for name in REQUIRED_GATES}
    statuses.update(dict(gates))
    ready = all(status == "pass" for status in statuses.values())
    return {
        "format": 1,
        "application": "AI Content Studio",
        "version": version,
        "commit": commit,
        "generated_at": (
            generated_at
            or datetime.now(timezone.utc).isoformat()
        ),
        "gates": statuses,
        "ready": ready,
    }


def write_evidence(path, evidence):
    destination = Path(path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    try:
        temporary.write_text(
            json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return destination


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate machine-readable release-candidate evidence"
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--version", default=read_version())
    parser.add_argument(
        "--gate",
        action="append",
        default=[],
        type=parse_gate,
        metavar="NAME=STATUS",
    )
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="return a failure status unless every required gate passed",
    )
    args = parser.parse_args(argv)
    evidence = build_evidence(
        commit=args.commit,
        version=args.version,
        gates=args.gate,
    )
    write_evidence(args.output, evidence)
    if args.require_ready and not evidence["ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
