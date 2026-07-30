#!/usr/bin/env bash
# Send a Python build script to a running Blender Bridge and print its result.
#
# Usage:
#   blender-send.sh /abs/path/build.py          run a .py file in the live session
#   blender-send.sh -c 'print(len(bpy.data.objects))'   run inline code
#   blender-send.sh --ping                      check the bridge is up
#   blender-send.sh --state                     cheap scene summary as JSON
#
# The script runs INSIDE Blender on the main thread, so bpy.data writes are
# legal, the viewport updates, and snapshot()/render() work. The bridge returns
# the script's captured stdout and any traceback; this wrapper prints stdout,
# and on failure prints the traceback and exits non-zero.
#
# Env: BLENDER_BRIDGE_PORT (default 8736), BLENDER_SEND_TIMEOUT seconds
# (default 180; raise for heavy renders), OUT (forwarded so scripts can write
# exports/metrics/PNGs into it via the injected OUT global or os.environ["OUT"]).
set -euo pipefail

PORT="${BLENDER_BRIDGE_PORT:-8736}"
TIMEOUT="${BLENDER_SEND_TIMEOUT:-180}"
BASE="http://127.0.0.1:$PORT"

not_reachable() {
    echo "ERROR: bridge not reachable on 127.0.0.1:$PORT — open Blender with the" >&2
    echo "       blender-bridge installed (scripts/startup/blender_bridge.py), or" >&2
    echo "       paste scripts/blender-bridge.py into the Scripting editor and Run Script." >&2
    exit 1
}

if [ $# -lt 1 ]; then
    echo "usage: blender-send.sh <build.py> | -c '<code>' | --ping | --state" >&2
    exit 2
fi

case "$1" in
    --ping)
        curl -s -m 10 "$BASE/ping" || not_reachable
        echo
        exit 0
        ;;
    --state)
        curl -s -m 30 "$BASE/state" || not_reachable
        echo
        exit 0
        ;;
esac

OUT_JSON="${OUT:-}"
if [ "$1" = "-c" ]; then
    [ $# -ge 2 ] || { echo "usage: blender-send.sh -c '<code>'" >&2; exit 2; }
    payload=$(CODE="$2" OUT="$OUT_JSON" python3 -c \
        'import json,os;print(json.dumps({"code":os.environ["CODE"],"out":os.environ.get("OUT","")}))')
else
    [ -f "$1" ] || { echo "ERROR: script not found: $1" >&2; exit 2; }
    abs=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
    payload=$(SCRIPT="$abs" OUT="$OUT_JSON" python3 -c \
        'import json,os;print(json.dumps({"path":os.environ["SCRIPT"],"out":os.environ.get("OUT","")}))')
fi

resp=$(curl -s -m "$TIMEOUT" -X POST "$BASE/run" --data-binary "$payload") || not_reachable

# Print captured stdout, then the traceback (if any) to stderr; exit reflects ok.
printf '%s' "$resp" | python3 -c '
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
