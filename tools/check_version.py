#!/usr/bin/env python3
"""Check that a release tag matches the version in vpxconfig/__init__.py.

    tools/check_version.py v0.5        exits 0 when the tag is "v" + the version, 1 otherwise

The version is set in one place, vpxconfig/__init__.py. A release is a git tag "v<version>" (for example v0.5),
and the release workflow refuses to build a tag that doesn't match.
"""
import re
import sys
from pathlib import Path

INIT = Path(__file__).resolve().parent.parent / "vpxconfig" / "__init__.py"


def code_version():
    match = re.search(r'^__version__\s*=\s*"([^"]+)"', INIT.read_text(), re.M)
    if not match:
        sys.exit(f"no __version__ found in {INIT}")
    return match[1]


def main(argv):
    if len(argv) != 2:
        sys.exit("usage: check_version.py <tag, for example v0.5>")
    version = code_version()
    if not re.fullmatch(r"\d+\.\d+(\.\d+)?", version):
        sys.exit(f"the version {version!r} in vpxconfig/__init__.py must look like 0.5 or 0.5.1")
    tag = argv[1]
    if tag != f"v{version}":
        sys.exit(f"the tag {tag} does not match the version in vpxconfig/__init__.py (expected v{version}). "
                 "Change one of them so they agree.")
    print(f"tag {tag} matches version {version}")


if __name__ == "__main__":
    main(sys.argv)
