#!/usr/bin/env bash
# Send a script to a running Cavalry Bridge and wait for completion.
#
# Usage:
#   cavalry-send.sh /abs/path/script.js        run a JS file
#   cavalry-send.sh -c 'api.setFrame(10);'     run inline code
#   cavalry-send.sh --ping                     check the bridge is reachable
#
# Env: CAVALRY_BRIDGE_PORT (default 8731), CAVALRY_SEND_TIMEOUT seconds (default 30;
# raise it for frame-loop renders). Completion is detected via the bridge's status
# file; the final line of output is that status JSON ({"seq":N,"ok":true,...}).
set -euo pipefail

PORT="${CAVALRY_BRIDGE_PORT:-8731}"
TIMEOUT="${CAVALRY_SEND_TIMEOUT:-30}"
STATUS=/tmp/cavalry-bridge-status.json

if [ $# -lt 1 ]; then
    echo "usage: cavalry-send.sh <script.js> | -c '<code>' | --ping" >&2
    exit 2
fi

if [ "$1" = "--ping" ]; then
    if curl -s -m 3 "http://127.0.0.1:$PORT/get"; then echo; exit 0; fi
    echo "ERROR: bridge not reachable on 127.0.0.1:$PORT" >&2
    exit 1
fi

if [ "$1" = "-c" ]; then
    [ $# -ge 2 ] || { echo "usage: cavalry-send.sh -c '<code>'" >&2; exit 2; }
    payload=$(python3 -c 'import json,sys; print(json.dumps({"code": sys.argv[1]}))' "$2")
else
    # Guard locally: the bridge only logs "no file at ..." into Cavalry's Log
    # window, which the caller cannot see, and a missing *directory* would make
    # the cd below fail under set -e with a raw shell error.
    [ -f "$1" ] || { echo "ERROR: script not found: $1" >&2; exit 2; }
    abs=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
    payload=$(python3 -c 'import json,sys; print(json.dumps({"path": sys.argv[1]}))' "$abs")
fi

before=$(cat "$STATUS" 2>/dev/null || true)

if ! curl -s -m 5 -X POST "http://127.0.0.1:$PORT/post" --data-binary "$payload" >/dev/null; then
    echo "ERROR: bridge not reachable on 127.0.0.1:$PORT — is Cavalry running with Cavalry Bridge started?" >&2
    exit 1
fi

elapsed=0
while [ "$elapsed" -lt "$((TIMEOUT * 2))" ]; do
    now=$(cat "$STATUS" 2>/dev/null || true)
    if [ -n "$now" ] && [ "$now" != "$before" ]; then
        echo "$now"
        case "$now" in *'"ok":true'*) exit 0 ;; *) exit 1 ;; esac
    fi
    sleep 0.5
    elapsed=$((elapsed + 1))
done

echo "TIMEOUT after ${TIMEOUT}s — long render still running, or check Cavalry's Log window" >&2
exit 1
