#!/usr/bin/env bash
# Build the one-file executable into dist/.  Usage: tools/build.sh
#
# PyInstaller is installed into a virtual environment in .venv (created on the first run), never into the system Python.
# The result is dist/vpxconfig plus dist/vpxconfig.sha256, for whatever machine/architecture this runs on (PyInstaller
# bundles a real interpreter, so it can't cross-compile); the version is inside it (--version). The release workflow
# runs this natively on both amd64 and arm64 and renames each result with its architecture before publishing.
set -euo pipefail
cd "$(dirname "$0")/.."

[ -x .venv/bin/python ] || "${PYTHON:-python3}" -m venv .venv
.venv/bin/python -m pip install --quiet -r requirements-build.txt
.venv/bin/python -m PyInstaller --clean --noconfirm vpxconfig.spec

(cd dist && sha256sum vpxconfig > vpxconfig.sha256)
echo "built dist/vpxconfig ($(.venv/bin/python -c 'import vpxconfig; print(vpxconfig.__version__)'))"
