#!/usr/bin/env bash
# Start the GIMP GUI with its Script-Fu server listening, and wait until it is
# reachable. This is the only step that cannot be done remotely: the server has
# to be switched on from inside GIMP, either by this launch flag or by hand from
# Filters > Development > Script-Fu > Start Server... ("Development" stays
# English even on a localised GIMP).
#
# Usage: gimp-start.sh [--port N]
#
# Refuses to launch when GIMP is already running. A second instance would fight
# the first one over the same config and the user's unsaved work is in the one
# already open -- in that case start the server from the menu instead, which
# this script will tell you.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${GIMP_PORT:-10008}"
if [ "${1:-}" = "--port" ]; then PORT="${2:?--port needs a number}"; fi

# A real ping, not just an open port: when GIMP quits, its script-fu-server
# plug-in outlives it for a while and keeps the port bound, so a port check
# alone reports a live session that isn't there.
if python3 "$HERE/gimp_client.py" --port "$PORT" --ping 2>/dev/null; then
    exit 0
fi

GIMP_BIN=""
for candidate in /Applications/GIMP.app/Contents/MacOS/gimp "$(command -v gimp || true)"; do
    if [ -n "$candidate" ] && [ -x "$candidate" ]; then GIMP_BIN="$candidate"; break; fi
done
if [ -z "$GIMP_BIN" ]; then
    echo "ERROR: GIMP not found (looked for /Applications/GIMP.app and gimp on PATH)." >&2
    exit 1
fi

if pgrep -f "$GIMP_BIN" >/dev/null 2>&1; then
    cat >&2 <<EOF
GIMP is already running, but nothing is listening on port $PORT.
Do not start a second instance -- ask the user to turn the server on in the
session they already have open:

    Filters > Development > Script-Fu > Start Server...
    (Listen on 127.0.0.1, port $PORT)

Then re-run: gimp-send.sh --ping
EOF
    exit 1
fi

# --batch-interpreter is required in GIMP 3: without it GIMP does not know
# which language -b is written in and exits with a list of interpreters.
nohup "$GIMP_BIN" \
    --batch-interpreter plug-in-script-fu-eval \
    -b "(plug-in-script-fu-server RUN-NONINTERACTIVE \"127.0.0.1\" $PORT \"\")" \
    >/tmp/gimp-script-fu-server.log 2>&1 &

echo "launching GIMP (pid $!) with the Script-Fu server on 127.0.0.1:$PORT ..."
for _ in $(seq 1 120); do
    if python3 "$HERE/gimp_client.py" --port "$PORT" --ping 2>/dev/null; then
        exit 0
    fi
    sleep 1
done

echo "ERROR: GIMP did not open port $PORT within 120s; see /tmp/gimp-script-fu-server.log" >&2
exit 1
