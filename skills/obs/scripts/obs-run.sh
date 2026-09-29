#!/usr/bin/env bash
# Run a Python job against the running OBS Studio over obs-websocket v5 and print its output.
#
# Usage:
#   obs-run.sh /abs/path/job.py              run a .py file with obs, OUT, ARGS, helpers injected
#   obs-run.sh -c 'print(scene_names())'     run inline code
#   obs-run.sh --ping                        {"ok": true, "obsVersion": …} or {"ok": false, "error": …}
#   obs-run.sh --state                       scenes + items, inputs, outputs, video settings as JSON
#   obs-run.sh job.py --arg scene=Main       KEY=VALUE strings, read back as ARGS["scene"]
#
# The client is pure standard-library Python (scripts/obs_client.py): nothing to install,
# nothing to load inside OBS. OBS only has to have its WebSocket server enabled
# (Tools > WebSocket Server Settings).
#
# Env: OBS_HOST (default 127.0.0.1), OBS_PORT and OBS_PASSWORD (default: read from the local
# obs-websocket config), OBS_TIMEOUT seconds per request (default 30), OUT (output directory,
# injected as OUT). Exit: 0 ok, 1 job raised, 2 bad usage, 3 OBS not reachable.
set -euo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
py="${OBS_PYTHON:-$(command -v python3 || true)}"
[ -n "$py" ] || { echo "ERROR: python3 not found" >&2; exit 2; }
exec "$py" "$HERE/obs_run.py" "$@"
