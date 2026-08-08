from __future__ import annotations

import argparse
import sys
import traceback

from backend.runtime import write_diagnostics


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="AI Content Studio desktop application")
    parser.add_argument(
        "--diagnostics",
        metavar="PATH",
        help="write packaged-runtime diagnostics as JSON and exit",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.diagnostics:
        write_diagnostics(args.diagnostics)
        return 0

    try:
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
