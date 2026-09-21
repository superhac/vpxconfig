"""Running commands on the local system.

Only commands registered in COMMANDS can be run, they take no user input and are executed
without a shell, so the web UI can never make this process run arbitrary code.
"""
import glob
import os
import re
import subprocess

COMMAND_TIMEOUT = 5


def _session_env():
    """Environment for talking to the desktop session (the server may be started from a tty/ssh)."""
    env = os.environ.copy()
    runtime = env.get("XDG_RUNTIME_DIR")
    if runtime and not env.get("WAYLAND_DISPLAY"):
        sockets = sorted(p for p in glob.glob(os.path.join(runtime, "wayland-*")) if not p.endswith(".lock"))
        if sockets:
            env["WAYLAND_DISPLAY"] = os.path.basename(sockets[0])
    return env


def run(argv):
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=COMMAND_TIMEOUT,
                           env=_session_env(), stdin=subprocess.DEVNULL)
    except FileNotFoundError:
        return {"ok": False, "error": f"'{argv[0]}' is not installed", "stdout": "", "argv": argv}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"'{argv[0]}' timed out after {COMMAND_TIMEOUT}s", "stdout": "", "argv": argv}
    ok = p.returncode == 0
    return {"ok": ok, "error": "" if ok else (p.stderr.strip() or f"exit code {p.returncode}"),
            "stdout": p.stdout, "argv": argv}


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
        elif m := re.match(r"width: \d+ px, height: \d+ px, refresh: ([\d.]+) Hz", s):
            target["refresh"] = float(m[1])
        elif s.startswith("flags:") and "current" in s and "refresh" in target:
            entry(target["name"])["refresh_hz"] = target["refresh"]
    return outputs


def parse_wayland_outputs(text):
    """Monitors reported by `wayland-info -i output`, one dict each.

    The list itself is exactly what `grep -oP "description: '\\K[^']+"` prints: VPX stores the monitor
    *description* (e.g. 'LG Electronics LG HDR 4K 0x00025EAC (DP-2)') in the *Display keys. Size and
    position are added when the output has them, but never decide which monitors exist.
    """
    details = list(_parse_details(text).values())
    monitors = []
    for desc in dict.fromkeys(re.findall(r"description: '([^']+)'", text)):
        m = next((o for o in details if o["description"] == desc), None)
        if m is None:
            name = re.search(r"\(([^()]+)\)\s*$", desc)
            m = {"name": name[1] if name else desc, "description": desc, "x": 0, "y": 0, "width": 0, "height": 0,
                 "physical_width_mm": 0, "physical_height_mm": 0, "refresh_hz": 0.0}
        monitors.append(m)
    return sorted(monitors, key=lambda o: (o["x"], o["y"]))


def displays():
    """Connected monitors: wayland-info -i output | grep -oP "description: '\\K[^']+" (plus size/position)."""
    result = run(["wayland-info", "-i", "output"])
    result["command"] = "wayland-info -i output"
    result["displays"] = parse_wayland_outputs(result["stdout"]) if result["ok"] else []
    if result["ok"] and not result["displays"]:
        result.update(ok=False, error="wayland-info returned no monitors")
    del result["stdout"]
    return result


# name -> function returning a JSON-able dict. Add new detection helpers here.
COMMANDS = {
    "displays": displays,
}
