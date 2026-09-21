"""Folder listing for the file picker. Lists the machine the server runs on, not the browser's."""
import os
from pathlib import Path

MAX_ENTRIES = 5000


def list_dir(raw, show_hidden=True, show_all=False, nearest=False):
    """Contents of a folder (a file path lists its parent and reports the file as selected).

    Folders come first. Files are limited to names containing '.ini' unless show_all is set, so
    VPinballX.ini, VPinballX.ini.mine, backups and so on are all visible. With `nearest`, a folder that
    doesn't exist yet lists its closest existing parent instead (for choosing where to save a new file).
    """
    raw = (raw or "").strip()
    home = Path.home()
    path = Path(os.path.abspath(Path(raw).expanduser())) if raw else home
    if raw and not Path(raw).expanduser().is_absolute():
        raise ValueError("Enter a full path, starting with / or ~")
    selected = ""
    try:
        while nearest and not path.exists() and path != path.parent:
            path = path.parent
        if path.is_file():
            selected, path = path.name, path.parent
        if not path.is_dir():
            raise ValueError("No folder at that path")
        entries = []
        with os.scandir(path) as it:
            for e in it:
                try:
                    is_dir = e.is_dir()
                    if not is_dir and not e.is_file():
                        continue
                except OSError:
                    continue
                if not show_hidden and e.name.startswith("."):
                    continue
                if not is_dir and not show_all and ".ini" not in e.name.lower():
                    continue
                entries.append({"name": e.name, "dir": is_dir})
    except PermissionError:
        raise ValueError("Permission denied for that folder")
    except OSError as e:
        raise ValueError(e.strerror or "Cannot read that folder")
    entries.sort(key=lambda x: (not x["dir"], x["name"].lower()))
    parts = path.parts
    return {
        "path": str(path), "parent": str(path.parent) if path != path.parent else "", "home": str(home),
        "selected": selected, "truncated": len(entries) > MAX_ENTRIES, "entries": entries[:MAX_ENTRIES],
        "crumbs": [{"name": (Path(*parts[: i + 1]).name or "/"), "path": str(Path(*parts[: i + 1]))}
                   for i in range(len(parts))],
    }
