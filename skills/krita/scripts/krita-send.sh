#!/usr/bin/env bash
# Send a Python build script to a running Krita Bridge and print its result.
#
# Usage:
#   krita-send.sh /abs/path/build.py                run a .py file in the live session
#   krita-send.sh -c 'print(Krita.instance().version())'   run inline code
#   krita-send.sh --ping                            check the bridge is up
#
# The script runs INSIDE Krita on the GUI thread, so the canvas updates and the
# whole libkis API is safe to call. The bridge returns the script's captured
# stdout/stderr and any traceback; this wrapper prints the output, and on
# failure prints the traceback to stderr and exits non-zero.
#
# Env: KRITA_BRIDGE_PORT (default 8737), KRITA_SEND_TIMEOUT seconds (default
# 120; raise for big exports), OUT (forwarded so scripts can write exports and
# metrics into it via os.environ["OUT"] or the injected OUT global).
set -euo pipefail

PORT="${KRITA_BRIDGE_PORT:-8737}"
TIMEOUT="${KRITA_SEND_TIMEOUT:-120}"
BASE="http://127.0.0.1:$PORT"

if [ $# -lt 1 ]; then
    echo "usage: krita-send.sh <build.py> | -c '<code>' | --ping" >&2
    exit 2
fi

if [ "$1" = "--ping" ]; then
    if curl -s -m 3 "$BASE/ping"; then echo; exit 0; fi
    echo "ERROR: bridge not reachable on 127.0.0.1:$PORT" >&2
    exit 1
fi

OUT_JSON="${OUT:-}"
if [ "$1" = "-c" ]; then
    [ $# -ge 2 ] || { echo "usage: krita-send.sh -c '<code>'" >&2; exit 2; }
    payload=$(CODE="$2" OUT="$OUT_JSON" python3 -c \
        'import json,os;print(json.dumps({"code":os.environ["CODE"],"out":os.environ.get("OUT","")}))')
else
    [ -f "$1" ] || { echo "ERROR: script not found: $1" >&2; exit 2; }
    abs=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
    payload=$(SCRIPT="$abs" OUT="$OUT_JSON" python3 -c \
        'import json,os;print(json.dumps({"path":os.environ["SCRIPT"],"out":os.environ.get("OUT","")}))')
fi

resp=$(curl -s -m "$TIMEOUT" -X POST "$BASE/run" --data-binary "$payload") || {
    echo "ERROR: bridge not reachable on 127.0.0.1:$PORT — start Krita (with the" >&2
    echo "       krita_bridge plugin enabled), or run scripts/krita-install-bridge.sh." >&2
    exit 1
}

# Print captured output, then the traceback (if any) to stderr; exit reflects ok.
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
