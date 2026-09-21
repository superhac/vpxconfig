#!/usr/bin/env bash
# Smoke test of the built executable.  Usage: tools/smoke_test_exe.sh dist/vpinconfig [port]
#
# Set EXPECTED_VERSION (for example 0.6) to also require exactly that version.
#
# Starts it with a throw-away HOME and config folder (so nothing real is touched), then checks that it reports its
# version, serves the page and the wizard from its bundled files, and keeps the answers in the config folder.
set -euo pipefail
EXE=$(realpath "${1:?path to the executable}")
PORT=${2:-18111}
WORK=$(mktemp -d)
PID=""
cleanup() { [ -z "$PID" ] || kill "$PID" 2>/dev/null || true; rm -rf "$WORK"; }
trap cleanup EXIT

VERSION_LINE=$("$EXE" --version)
echo "version: $VERSION_LINE"
[[ "$VERSION_LINE" =~ ^VPinConfig\ [0-9]+\.[0-9]+ ]] || { echo "unexpected --version output"; exit 1; }
if [ -n "${EXPECTED_VERSION:-}" ] && [ "$VERSION_LINE" != "VPinConfig $EXPECTED_VERSION" ]; then
  echo "expected version $EXPECTED_VERSION but the executable says: $VERSION_LINE"; exit 1
fi

export HOME="$WORK/home" XDG_CONFIG_HOME="$WORK/config"
mkdir -p "$HOME"
"$EXE" --port "$PORT" >"$WORK/log" 2>&1 &
PID=$!

for _ in $(seq 1 100); do
  curl -fs "http://127.0.0.1:$PORT/api/steps" >/dev/null 2>&1 && break
  kill -0 "$PID" 2>/dev/null || { echo "the executable exited early:"; cat "$WORK/log"; exit 1; }
  sleep 0.2
done

curl -fs "http://127.0.0.1:$PORT/" | grep -q "<title>VPinConfig</title>"
curl -fs "http://127.0.0.1:$PORT/app.js" | grep -q "describeMapping\|mappingControl"
curl -fs "http://127.0.0.1:$PORT/keys.js" | grep -q "KEY_BY_CODE"

python3 - "$PORT" "$WORK" <<'PY'
import json, sys, urllib.request
port, work = sys.argv[1], sys.argv[2]
get = lambda p: json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}{p}"))
steps = get("/api/steps")
fields = [f for s in steps["steps"] for g in s["groups"] for f in g["fields"]]
assert steps["version"], "no version"
assert len(steps["steps"]) >= 20 and len(fields) >= 150, (len(steps["steps"]), len(fields))       # the bundled base ini was read
assert steps["steps"][0]["id"] == "start" and steps["steps"][-1]["id"] == "review"
preview = get("/api/preview")
assert preview["changes"] == [] and preview["problems"] == [], preview["changes"]            # a fresh start shows no changes
req = urllib.request.Request(f"http://127.0.0.1:{port}/api/state", method="PUT", data=json.dumps({"values": {"Player.BGSet": "1"}}).encode(),
                             headers={"Content-Type": "application/json", "X-VPX-Config": "1"})
urllib.request.urlopen(req)
state = json.load(open(f"{work}/config/vpinconfig/state.json"))                                # kept in the config folder
assert state["values"]["Player.BGSet"] == "1"
assert [c["key"] for c in get("/api/preview")["changes"]] == ["BGSet"]
print(f"steps: {len(steps['steps'])}, fields: {len(fields)}, version {steps['version']}, state kept in the config folder")
PY
echo "smoke test passed"
