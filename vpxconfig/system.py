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
    """Best-effort geometry per monitor from `wayland-info -i output`, keyed by connector name."""
    outputs, xdg, wl = {}, None, None

    def entry(name):
        return outputs.setdefault(name, {"name": name, "description": "", "x": 0, "y": 0, "width": 0,
                                         "height": 0, "physical_width_mm": 0, "physical_height_mm": 0,
                                         "refresh_hz": 0.0})

    for line in text.splitlines():
        s = line.strip()
        if line.startswith("interface:"):
            xdg, wl = None, ({} if "'wl_output'" in line else None)
            continue
        if s == "xdg_output_v1":
            xdg = {}
            continue
        target = xdg if xdg is not None else wl
        if target is None:
            continue
        if m := re.match(r"name: '?(.+?)'?$", s):
            target["name"] = m[1]
            entry(m[1])
        elif "name" not in target:
            continue
        elif m := re.match(r"description: '?(.+?)'?$", s):
            entry(target["name"])["description"] = m[1]
        elif m := re.match(r"logical_x: (-?\d+), logical_y: (-?\d+)", s):
            entry(target["name"]).update(x=int(m[1]), y=int(m[2]))
        elif m := re.match(r"logical_width: (\d+), logical_height: (\d+)", s):
            entry(target["name"]).update(width=int(m[1]), height=int(m[2]))
        elif m := re.match(r"physical_width: (\d+) mm, physical_height: (\d+) mm", s):
            entry(target["name"]).update(physical_width_mm=int(m[1]), physical_height_mm=int(m[2]))
        elif m := re.match(r"width: (\d+) px, height: (\d+) px, refresh: ([\d.]+) Hz", s):
            target["refresh"], target["mode"] = float(m[3]), (int(m[1]), int(m[2]))
        elif s.startswith("flags:") and "current" in s and "refresh" in target:
            entry(target["name"])["refresh_hz"] = target["refresh"]
            entry(target["name"])["_mode"] = target["mode"]
    for o in outputs.values():                     # no xdg_output block: use the size of the current mode
        mode = o.pop("_mode", None)
        if mode and not o["width"]:
            o["width"], o["height"] = mode
    return outputs


def parse_wayland_outputs(text):
    """Monitors reported by `wayland-info -i output`, one dict each.

    The list itself is exactly what `grep -oP "description: '\\K[^']+"` prints: VPX stores the monitor
    *description* (e.g. 'LG Electronics LG HDR 4K 0x00025EAC (DP-2)') in the *Display keys. Size and
    position are added when the output has them, but never decide which monitors exist.
    """
    details = list(_parse_details(text).values())
    monitors = []
    descriptions = re.findall(r"description: '([^']+)'", text)
    if not descriptions:                           # older wayland-info builds print them unquoted (wl_output blocks)
        descriptions = re.findall(r"^\s*description: (.+?)\s*$", text, re.M)
    for desc in dict.fromkeys(descriptions):
        m = next((o for o in details if o["description"] == desc), None)
        if m is None:
            name = re.search(r"\(([^()]+)\)\s*$", desc)
            m = {"name": name[1] if name else desc, "description": desc, "x": 0, "y": 0, "width": 0, "height": 0,
                 "physical_width_mm": 0, "physical_height_mm": 0, "refresh_hz": 0.0}
        monitors.append(m)
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
