"""Running commands on the local system.

Only commands registered in COMMANDS can be run, they take no user input and are executed
without a shell, so the web UI can never make this process run arbitrary code.
"""
import glob
import os
import re
import shutil
import subprocess
import sys

COMMAND_TIMEOUT = 5


def _wayland_sockets(runtime):
    return sorted(os.path.basename(p) for p in glob.glob(os.path.join(runtime, "wayland-*")) if not p.endswith(".lock"))


def _session_env(display=None):
    """Environment for a child program. `display` picks the Wayland socket to talk to."""
    env = os.environ.copy()
    if getattr(sys, "frozen", False):
        # The PyInstaller executable points LD_LIBRARY_PATH at its own bundled libraries; other programs must not inherit that.
        original = env.pop("LD_LIBRARY_PATH_ORIG", None)
        if original is not None:
            env["LD_LIBRARY_PATH"] = original
        else:
            env.pop("LD_LIBRARY_PATH", None)
    if display:
        env["WAYLAND_DISPLAY"] = display
    return env


def run(argv, display=None):
    result = {"ok": False, "error": "", "stdout": "", "stderr": "", "exit_code": None, "argv": argv}
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=COMMAND_TIMEOUT,
                           env=_session_env(display), stdin=subprocess.DEVNULL)
    except FileNotFoundError:
        return {**result, "error": f"'{argv[0]}' is not installed"}
    except subprocess.TimeoutExpired:
        return {**result, "error": f"'{argv[0]}' timed out after {COMMAND_TIMEOUT}s"}
    ok = p.returncode == 0
    return {**result, "ok": ok, "error": "" if ok else (p.stderr.strip() or f"exit code {p.returncode}"),
            "stdout": p.stdout, "stderr": p.stderr, "exit_code": p.returncode}


def _parse_details(text):
    """Everything `wayland-info -i output` says about each monitor, keyed by the compositor's global id.

    The wl_output block (advertised version, description, geometry make/model/position, modes) and the xdg_output block
    (name, description, logical position/size; tied to it by its `output: <id>` line) of one monitor are merged.
    """
    outputs, names = {}, {}
    cur = None                                             # ("wl" | "xdg", key) of the block being read

    def entry(key):
        return outputs.setdefault(key, {"name": f"output-{key}", "description": "", "x": 0, "y": 0, "width": 0, "height": 0,
                                        "physical_width_mm": 0, "physical_height_mm": 0, "refresh_hz": 0.0,
                                        "_wl_version": None, "_wl_description": "", "_xdg_description": "", "_model": "",
                                        "_make": ""})

    for line in text.splitlines():
        s = line.strip()
        if line.startswith("interface:"):
            cur = None
            if "'wl_output'" in line:
                m = re.search(r"version:\s*(\d+).*?name:\s*(\d+)", line)
                key = m[2] if m else f"wl{len(outputs)}"
                entry(key)["_wl_version"] = int(m[1]) if m else None
                cur = ("wl", key)
            continue
        if s == "xdg_output_v1":
            cur = ("xdg", None)
            continue
        if cur is None:
            continue
        kind, key = cur
        if kind == "xdg" and key is None:
            if m := re.match(r"output: (\d+)", s):
                cur = ("xdg", m[1])
                entry(m[1])
                continue
            if m := re.match(r"name: '?(.+?)'?$", s):      # no `output:` line: find the monitor by its connector name
                cur = ("xdg", names.get(m[1]) or m[1])
                entry(cur[1])["name"] = m[1]
            else:
                continue
            key = cur[1]
        e = entry(key)
        if m := re.match(r"name: '?(.+?)'?$", s):
            e["name"] = m[1]
            names[m[1]] = key
        elif m := re.match(r"description: '?(.+?)'?$", s):
            e["_xdg_description" if kind == "xdg" else "_wl_description"] = m[1]
        elif s.startswith("make:") and (m := re.search(r"make: '([^']*)', model: '([^']*)'", s)):
            e["_make"], e["_model"] = m[1], m[2]
        elif m := re.match(r"logical_x: (-?\d+), logical_y: (-?\d+)", s):
            e.update(x=int(m[1]), y=int(m[2]), _logical=True)
        elif m := re.match(r"x: (-?\d+), y: (-?\d+)", s):                # wl_output geometry: used when there is no logical position
            if not e.get("_logical"):
                e.update(x=int(m[1]), y=int(m[2]))
        elif m := re.match(r"logical_width: (\d+), logical_height: (\d+)", s):
            e.update(width=int(m[1]), height=int(m[2]))
        elif m := re.match(r"physical_width: (\d+) mm, physical_height: (\d+) mm", s):
            e.update(physical_width_mm=int(m[1]), physical_height_mm=int(m[2]))
        elif m := re.match(r"width: (\d+) px, height: (\d+) px, refresh: ([\d.]+) Hz", s):
            cur_mode = (float(m[3]), (int(m[1]), int(m[2])))
            e["_pending_mode"] = cur_mode
        elif s.startswith("flags:") and "current" in s and e.get("_pending_mode"):
            e["refresh_hz"], e["_mode"] = e["_pending_mode"][0], e["_pending_mode"][1]
    for o in outputs.values():
        for private in ("_logical", "_pending_mode"):
            o.pop(private, None)
        mode = o.pop("_mode", None)
        if mode and not o["width"]:                # no xdg_output block: use the size of the current mode
            o["width"], o["height"] = mode
    return outputs


def sdl_display_name(o):
    """The name SDL 3.4 gives a monitor on Wayland (SDL_waylandvideo.c), which is what VPX puts in its display id.

    wl_output version 4 or newer (SDL binds min(advertised, 4)): the wl_output description; the xdg_output description
    is ignored ("deprecated as of wl_output v4"). Older wl_output: the xdg_output description. In both cases the
    wl_output geometry `model` is the fallback when there is no description.
    Returns (name, where it came from).
    """
    version = o["_wl_version"]
    if version is not None and version >= 4:
        if o["_wl_description"]:
            return o["_wl_description"], "wl_output description"
    elif o["_xdg_description"]:
        return o["_xdg_description"], "xdg_output description"
    if o["_model"]:
        return o["_model"], "wl_output model"
    return o["_wl_description"] or o["_xdg_description"], "description (not what SDL would use)"


def display_id(description, x, y):
    """What VPX writes in PlayfieldDisplay, BackglassDisplay, ...: "<display name> [x, y]", with the display's logical
    position in the desktop layout (Window.cpp: std::format("{} [{}, {}]", name, bounds.x, bounds.y)). VPX compares the
    setting to this string exactly, so a value without the position matches nothing."""
    return f"{description} [{x}, {y}]"


def parse_wayland_outputs(text):
    """Monitors reported by `wayland-info -i output`, one dict each.

    `description` is the display name SDL (and so VPX) uses, chosen like SDL does (see sdl_display_name); `name_source`
    says which field it came from. `id` is the value for the *Display keys: that name plus the logical position,
    "LG HDR 4K [1920, 0]". On a compositor that reports a description, this is the same text that
    `grep -oP "description: '\\K[^']+"` prints.
    """
    monitors = []
    for o in _parse_details(text).values():
        name, source = sdl_display_name(o)
        if not name:
            continue
        m = {k: v for k, v in o.items() if not k.startswith("_")}
        m.update(description=name, name_source=source, id=display_id(name, o["x"], o["y"]),
                 model=o["_model"], make=o["_make"], wl_output_version=o["_wl_version"])
        monitors.append(m)
    if not monitors:                               # no interface blocks at all: fall back to the descriptions in the text
        descriptions = re.findall(r"description: '([^']+)'", text) or re.findall(r"^\s*description: (.+?)\s*$", text, re.M)
        for desc in dict.fromkeys(descriptions):
            name = re.search(r"\(([^()]+)\)\s*$", desc)
            monitors.append({"name": name[1] if name else desc, "description": desc, "name_source": "description", "x": 0, "y": 0,
                             "width": 0, "height": 0, "physical_width_mm": 0, "physical_height_mm": 0, "refresh_hz": 0.0,
                             "id": display_id(desc, 0, 0), "model": "", "make": "", "wl_output_version": None})
    return sorted(monitors, key=lambda o: (o["x"], o["y"]))


def _candidate_displays():
    """The WAYLAND_DISPLAY of the environment first (what the user's own session uses), then every other socket in
    XDG_RUNTIME_DIR: a machine can have several compositors, and the first one is not always the one with the monitors."""
    runtime = os.environ.get("XDG_RUNTIME_DIR", "")
    current = os.environ.get("WAYLAND_DISPLAY", "")
    found = ([current] if current else []) + (_wayland_sockets(runtime) if runtime else [])
    return list(dict.fromkeys(found)) or [None]


def displays():
    """Connected monitors: wayland-info -i output | grep -oP "description: '\\K[^']+" (plus size/position).

    Every Wayland socket is tried until one reports monitors, and what was run and seen is returned in `diagnostics`.
    """
    runtime = os.environ.get("XDG_RUNTIME_DIR", "")
    diagnostics = {"wayland_info": shutil.which("wayland-info") or "not found in PATH",
                   "WAYLAND_DISPLAY": os.environ.get("WAYLAND_DISPLAY", "(not set)"),
                   "XDG_RUNTIME_DIR": runtime or "(not set)", "sockets": _wayland_sockets(runtime) if runtime else [],
                   "tried": []}
    runs = []
    for display in _candidate_displays():
        result = run(["wayland-info", "-i", "output"], display)
        monitors = parse_wayland_outputs(result["stdout"]) if result["ok"] else []
        lines = result["stdout"].splitlines()
        diagnostics["tried"].append({"WAYLAND_DISPLAY": display or "(not set)", "exit_code": result["exit_code"],
                                     "error": result["error"], "output_lines": len(lines), "monitors": len(monitors),
                                     "output_start": lines[:8], "stderr": result["stderr"].strip()[:300]})
        runs.append((display, result))
        if monitors:
            return {"ok": True, "error": "", "displays": monitors, "argv": result["argv"], "command": "wayland-info -i output",
                    "wayland_display": display or "", "diagnostics": diagnostics}
    connected = [d or "(default)" for d, r in runs if r["ok"]]
    if connected:
        error = "wayland-info connected (" + ", ".join(connected) + ") but its output lists no monitors"
    else:
        error = runs[0][1]["error"] + (f" (also tried: {', '.join(d for d, _ in runs[1:])})" if len(runs) > 1 else "")
    return {"ok": False, "error": error, "displays": [], "argv": runs[0][1]["argv"], "command": "wayland-info -i output",
            "wayland_display": "", "diagnostics": diagnostics}


# name -> function returning a JSON-able dict. Add new detection helpers here.
COMMANDS = {
    "displays": displays,
}
