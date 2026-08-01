#!/usr/bin/env bash
# Run a Python build script inside the RUNNING GIMP and print what it printed.
#
# Usage:
#   gimp-send.sh /abs/path/build.py           run a .py file in the live session
#   gimp-send.sh -c 'print(Gimp.version())'   run inline Python
#   gimp-send.sh --ping                       check GIMP + its Script-Fu server
#   gimp-send.sh --scheme '(gimp-version)'    evaluate raw Script-Fu
#
# The script is executed by GIMP's own python-fu-eval, so it drives the images
# the user is looking at: canvases update, the layer stack is theirs, and
# nothing runs headless. stdout/stderr and any traceback come back here, and a
# non-zero exit means the script raised.
#
# Env: GIMP_HOST (127.0.0.1), GIMP_PORT (10008), GIMP_SEND_TIMEOUT seconds
# (120 -- raise it for big exports or batch runs), OUT (a directory the script
# receives as an OUT global and os.environ["OUT"]; put exports, metrics and
# check images there so they can be read back).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLIENT="$HERE/gimp_client.py"

if [ $# -lt 1 ]; then
    echo "usage: gimp-send.sh <build.py> | -c '<code>' | --scheme '<expr>' | --ping" >&2
    exit 2
fi

common=(--host "${GIMP_HOST:-127.0.0.1}" --port "${GIMP_PORT:-10008}"
        --timeout "${GIMP_SEND_TIMEOUT:-120}")

case "$1" in
    --ping)
        exec python3 "$CLIENT" "${common[@]}" --ping
        ;;
    --scheme)
        [ $# -ge 2 ] || { echo "usage: gimp-send.sh --scheme '<expr>'" >&2; exit 2; }
        exec python3 "$CLIENT" "${common[@]}" --scheme "$2"
        ;;
    -c)
        [ $# -ge 2 ] || { echo "usage: gimp-send.sh -c '<code>'" >&2; exit 2; }
        exec python3 "$CLIENT" "${common[@]}" --out "${OUT:-}" --code "$2"
        ;;
    *)
        [ -f "$1" ] || { echo "ERROR: script not found: $1" >&2; exit 2; }
        exec python3 "$CLIENT" "${common[@]}" --out "${OUT:-}" --python "$1"
        ;;
esac
