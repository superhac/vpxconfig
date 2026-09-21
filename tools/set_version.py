#!/usr/bin/env python3
"""Set the version of a build: rewrites __version__ in vpinconfig/__init__.py.

    tools/set_version.py 0.6           (a leading "v" is accepted: v0.6)

The release workflow uses this when it is started by hand with a version typed into the "Run workflow" form, so the
executable reports that version without anyone editing the code first (the change exists only in that run's checkout).
"""
import re
import sys
from pathlib import Path

INIT = Path(__file__).resolve().parent.parent / "vpinconfig" / "__init__.py"
VERSION = re.compile(r"\d+\.\d+(\.\d+)?")


def normalise(text):
    """'v0.6' or ' 0.6 ' -> '0.6'. Raises ValueError unless the result looks like 0.6 or 0.6.1."""
    version = text.strip().removeprefix("v")
    if not VERSION.fullmatch(version):
        raise ValueError(f"{text!r} is not a version: use something like 0.6 or 0.6.1")
    return version


def with_version(source, version):
    new, count = re.subn(r'^(__version__\s*=\s*)"[^"]*"', lambda m: f'{m[1]}"{version}"', source, count=1, flags=re.M)
    if count != 1:
        raise ValueError("no __version__ line found")
    return new


def main(argv):
    if len(argv) not in (2, 3):
        sys.exit("usage: set_version.py <version, for example 0.6> [file]")
    path = Path(argv[2]) if len(argv) == 3 else INIT
    try:
        version = normalise(argv[1])
        path.write_text(with_version(path.read_text(), version))
    except ValueError as e:
        sys.exit(str(e))
    print(f"version set to {version}")


if __name__ == "__main__":
    main(sys.argv)
