#!/usr/bin/env bash
# Start OBS Studio (if it is not running) and wait until obs-websocket answers.
#
# Usage: obs-start.sh [--collection NAME] [--profile NAME] [--scene NAME]
#
# The three flags are OBS launch parameters: they pick the scene collection, profile and
# starting scene for this session — use --collection after obs_collection.py install.
# The WebSocket server itself cannot be switched on from outside: if OBS starts but the
# port stays closed, the user has to enable it once in Tools > WebSocket Server Settings.
#
# Refuses to launch a second instance: when OBS is already running, the flags cannot apply
# and the user's live session is in the open one.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
obs_args=()
while [ $# -gt 0 ]; do
    case "$1" in
        --collection | --profile | --scene)
            [ $# -ge 2 ] || { echo "ERROR: $1 needs a value" >&2; exit 2; }
            obs_args+=("$1" "$2")
            shift 2
            ;;
        *)
            echo "ERROR: unknown argument $1 (usage: obs-start.sh [--collection N] [--profile N] [--scene N])" >&2
            exit 2
            ;;
    esac
done

if bash "$HERE/obs-run.sh" --ping 2>/dev/null | grep -q '"ok": true'; then
    [ ${#obs_args[@]} -eq 0 ] || echo "note: OBS is already running; launch flags ignored" >&2
    bash "$HERE/obs-run.sh" --ping
    exit 0
fi

if pgrep -xq obs 2>/dev/null || pgrep -xq OBS 2>/dev/null; then
    cat >&2 <<EOF
OBS is running, but obs-websocket does not answer. Do not start a second instance —
ask the user to open, in the OBS window they already have:

    Tools > WebSocket Server Settings > Enable WebSocket server   (port 4455)

and, if authentication is on, to share the password via OBS_PASSWORD (Show Connect Info).
Then re-run: obs-run.sh --ping
EOF
    exit 3
fi

case "$(uname -s)" in
    Darwin)
        [ -d /Applications/OBS.app ] || { echo "ERROR: /Applications/OBS.app not found" >&2; exit 1; }
        open -a OBS --args ${obs_args[@]+"${obs_args[@]}"}
        ;;
    *)
        command -v obs >/dev/null || { echo "ERROR: obs not found on PATH" >&2; exit 1; }
        nohup obs ${obs_args[@]+"${obs_args[@]}"} >/tmp/obs-start.log 2>&1 &
        ;;
esac

echo "launching OBS, waiting for obs-websocket ..." >&2
for _ in $(seq 1 60); do
    out=$(bash "$HERE/obs-run.sh" --ping 2>/dev/null || true)
    if printf '%s' "$out" | grep -q '"ok": true'; then
        printf '%s\n' "$out"
        exit 0
    fi
    sleep 1
done

cat >&2 <<EOF
ERROR: OBS started but obs-websocket did not answer within 60s. Last ping: ${out:-none}
       On a fresh install the server is off: ask the user to enable it in
       Tools > WebSocket Server Settings (and to dismiss the first-run wizard if shown).
EOF
exit 3
