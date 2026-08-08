from __future__ import annotations

import argparse
import json
import os
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
    modes.add_argument(
        "--smoke-update-ui",
        metavar="PATH",
        help="open the packaged update UI without network access and write a report",
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


def _restore_environment(name, previous):
    if previous is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = previous


def run_gui_smoke(path):
    from PySide6.QtCore import QTimer
    from desktop.app import AIContentStudio

    name = "AI_CONTENT_STUDIO_DISABLE_UPDATE_CHECKS"
    previous = os.environ.get(name)
    os.environ[name] = "1"
    try:
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
                "network_update_checks_disabled": True,
                "exit_code": exit_code,
            },
        )
        return exit_code
    finally:
        _restore_environment(name, previous)


def run_update_ui_smoke(path):
    from PySide6.QtCore import QTimer
    from desktop.app import AIContentStudio

    name = "AI_CONTENT_STUDIO_DISABLE_UPDATE_CHECKS"
    previous = os.environ.get(name)
    os.environ[name] = "1"
    try:
        app = AIContentStudio()
        app.window.open_update_dialog(check=False)
        dialog = app.window.update_dialog
        action = getattr(app.window, "updateAction", None)
        QTimer.singleShot(750, app.qt.quit)
        exit_code = app.run()
        write_json_report(
            path,
            {
                "application": "AI Content Studio",
                "version": VERSION,
                "update_action_available": bool(
                    action is not None and action.text() == "Check for Updates..."
                ),
                "update_dialog_created": dialog is not None,
                "network_update_checks_disabled": True,
                "shutdown": True,
                "exit_code": exit_code,
            },
        )
        return exit_code
    finally:
        _restore_environment(name, previous)


def main(argv=None):
    args = parse_args(argv)
    if args.diagnostics:
        write_diagnostics(args.diagnostics)
        return 0

    try:
        if args.smoke_gui:
            return run_gui_smoke(args.smoke_gui)
        if args.smoke_update_ui:
            return run_update_ui_smoke(args.smoke_update_ui)

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
