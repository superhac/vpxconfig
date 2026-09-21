#!/usr/bin/env bash
# Build the one-file executable into dist/.  Usage: tools/build.sh
#
# PyInstaller is installed into a virtual environment in .venv (created on the first run), never into the system Python.
# The result is dist/vpinconfig (Linux x86_64 only) plus dist/vpinconfig.sha256; the version is inside it (--version).
set -euo pipefail
cd "$(dirname "$0")/.."

[ -x .venv/bin/python ] || "${PYTHON:-python3}" -m venv .venv
.venv/bin/python -m pip install --quiet -r requirements-build.txt
.venv/bin/python -m PyInstaller --clean --noconfirm vpinconfig.spec

(cd dist && sha256sum vpinconfig > vpinconfig.sha256)
echo "built dist/vpinconfig ($(.venv/bin/python -c 'import vpinconfig; print(vpinconfig.__version__)'))"
