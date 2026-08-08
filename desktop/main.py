from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

from backend.runtime import write_diagnostics
from backend.version import VERSION


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="AI Content Studio desktop application")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--diagnostics",
        metavar="PATH",
        help="write packaged-runtime diagnostics as JSON and exit",
    )
    modes.add_argument(
        "--smoke-gui",
        metavar="PATH",
        help="start the GUI, perform a clean timed shutdown, and write a JSON report",
    )
    return parser.parse_args(argv)


def write_json_report(path, data):
    destination = Path(path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(destination)
    return destination


def run_gui_smoke(path):
    from PySide6.QtCore import QTimer
    from desktop.app import AIContentStudio

    app = AIContentStudio()
    QTimer.singleShot(750, app.qt.quit)
    exit_code = app.run()
    write_json_report(
        path,
        {
            "application": "AI Content Studio",
            "version": VERSION,
            "started": True,
            "shutdown": True,
            "exit_code": exit_code,
        },
    )
    return exit_code


def main(argv=None):
    args = parse_args(argv)
    if args.diagnostics:
        write_diagnostics(args.diagnostics)
        return 0

    try:
        if args.smoke_gui:
            return run_gui_smoke(args.smoke_gui)

        from desktop.app import AIContentStudio

        app = AIContentStudio()
        return app.run()
    except Exception as error:
        print("Application startup failed:", file=sys.stderr)
        print(error, file=sys.stderr)
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
