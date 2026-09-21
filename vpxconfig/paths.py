"""Where VPXConfig finds its bundled files and keeps its state.

Run from source, everything is in the project folder. Run as a PyInstaller one-file executable, the read-only files
that are bundled inside it (the web pages and the base VPinballX.ini) are in the temporary folder the executable
unpacks itself into, and the state file goes to the user's config folder, because that temporary folder is deleted
when the program exits.
"""
import os
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent


def frozen():
    return bool(getattr(sys, "frozen", False))


def resource_dir():
    """Folder holding the bundled `web/` and `VPinballX.ini`."""
    return Path(getattr(sys, "_MEIPASS", PROJECT)) if frozen() else PROJECT


def state_path():
    """Where the wizard answers are kept between runs."""
    if not frozen():
        return PROJECT / "state.json"
    base = os.environ.get("XDG_CONFIG_HOME", "")
    config = Path(base) if base and Path(base).is_absolute() else Path.home() / ".config"
    return config / "vpxconfig" / "state.json"
