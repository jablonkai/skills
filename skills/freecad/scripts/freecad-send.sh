#!/usr/bin/env bash
# Send a Python build script to a running FreeCAD Bridge and print its result.
#
# Usage:
#   freecad-send.sh /abs/path/build.py       run a .py file in the live session
#   freecad-send.sh -c 'App.newDocument("x")'   run inline code
#   freecad-send.sh --ping                   check the bridge is up
#
# The script runs INSIDE FreeCAD on the GUI thread, so the viewport updates and
# Gui.*/saveImage work. The bridge returns the script's captured stdout and any
# traceback; this wrapper prints stdout, and on failure prints the traceback and
# exits non-zero.
#
# Env: FREECAD_BRIDGE_PORT (default 8735), FREECAD_SEND_TIMEOUT seconds
# (default 120; raise for heavy builds), OUT (forwarded so scripts can write
# exports/metrics into it via os.environ["OUT"] or the injected OUT global).
set -euo pipefail

PORT="${FREECAD_BRIDGE_PORT:-8735}"
TIMEOUT="${FREECAD_SEND_TIMEOUT:-120}"
BASE="http://127.0.0.1:$PORT"

if [ $# -lt 1 ]; then
    echo "usage: freecad-send.sh <build.py> | -c '<code>' | --ping" >&2
    exit 2
fi

if [ "$1" = "--ping" ]; then
    if curl -s -m 3 "$BASE/ping"; then echo; exit 0; fi
    echo "ERROR: bridge not reachable on 127.0.0.1:$PORT" >&2
    exit 1
fi

OUT_JSON="${OUT:-}"
if [ "$1" = "-c" ]; then
    [ $# -ge 2 ] || { echo "usage: freecad-send.sh -c '<code>'" >&2; exit 2; }
    payload=$(CODE="$2" OUT="$OUT_JSON" python3 -c \
        'import json,os;print(json.dumps({"code":os.environ["CODE"],"out":os.environ.get("OUT","")}))')
else
    [ -f "$1" ] || { echo "ERROR: script not found: $1" >&2; exit 2; }
    abs=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
    payload=$(SCRIPT="$abs" OUT="$OUT_JSON" python3 -c \
        'import json,os;print(json.dumps({"path":os.environ["SCRIPT"],"out":os.environ.get("OUT","")}))')
fi

resp=$(curl -s -m "$TIMEOUT" -X POST "$BASE/run" --data-binary "$payload") || {
    echo "ERROR: bridge not reachable on 127.0.0.1:$PORT — open FreeCAD and run the" >&2
    echo "       freecad-bridge macro (Macro ▸ Macros ▸ freecad-bridge ▸ Execute)." >&2
    exit 1
}

# Print captured stdout, then the traceback (if any) to stderr; exit reflects ok.
printf '%s' "$resp" | RESP_TIMEOUT="$TIMEOUT" python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.stderr.write("ERROR: malformed bridge response\n"); sys.exit(1)
out = (d.get("output") or "").rstrip()
if out:
    print(out)
if not d.get("ok", False):
    sys.stderr.write((d.get("error") or "script failed") + "\n")
    sys.exit(1)
'
