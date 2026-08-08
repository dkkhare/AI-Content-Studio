from __future__ import annotations

import argparse
import ast
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "backend" / "version.py"
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def read_version(path=VERSION_FILE):
    tree = ast.parse(Path(path).read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "VERSION" for target in node.targets)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            version = node.value.value
            if not SEMVER.fullmatch(version):
                raise ValueError(f"VERSION must use major.minor.patch: {version}")
            return version
    raise ValueError(f"VERSION string not found in {path}")


def validate_tag(tag, version):
    expected = f"v{version}"
    if tag != expected:
        raise ValueError(f"Release tag {tag!r} does not match application version {expected!r}.")
    return tag


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read and validate the application release version")
    parser.add_argument("--tag", help="validate a release tag such as v0.19.0")
    args = parser.parse_args(argv)
    version = read_version()
    if args.tag:
        validate_tag(args.tag, version)
    print(version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
