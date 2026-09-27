#!/usr/bin/env bash
# Render a Motion IO events file to image frames and return when it is done.
#
# Rebelle Motion IO does not exit after a batch on macOS (it sits there with its
# window open), and it prints progress rather than any exit status, so this
# wrapper watches the log for the final "batch frame end: N/N" line, then stops
# the app itself. Without that, every batch call would hang until a timeout.
#
# Usage:
#   rebelle-batch.sh EVENTS.json OUTDIR [extra Rebelle args...]
#
#   OUTDIR gets frame_0000.png ... plus rebelle.log (the raw app output).
#   Extra args are passed straight through, e.g. to add data layers:
#     rebelle-batch.sh a.json out -batch-out-bump "$PWD/out/bump_####.exr"
#
# Env:
#   REBELLE_MOTION_IO   path to the Motion IO binary (default: /Applications/...)
#   REBELLE_TIMEOUT     seconds to wait for the render (default 900)
#   REBELLE_OUT_PATTERN output pattern (default "$OUTDIR/frame_####.png")

set -euo pipefail

app=${REBELLE_MOTION_IO:-"/Applications/Rebelle 8 Motion IO.app/Contents/MacOS/Rebelle 8 Motion IO"}
timeout=${REBELLE_TIMEOUT:-900}

if [[ $# -lt 2 ]]; then
  sed -n '2,25p' "$0" >&2
  exit 2
fi

events=$1
outdir=$2
shift 2

[[ -f "$events" ]] || { echo "no such events file: $events" >&2; exit 2; }
[[ -x "$app" ]] || { echo "Motion IO not found at: $app (set REBELLE_MOTION_IO, or render live with rebelle_ws.py --send EVENTS --frames-out DIR)" >&2; exit 2; }
# The Pro build accepts -batch-json and then ignores it (verified 8.3.4): it just
# opens a blank artwork and never prints a frame. Fail fast instead of timing out.
case "$app" in
  *"Motion IO"*) ;;
  *) echo "warning: $app does not look like Motion IO; Rebelle Pro silently ignores -batch-json" >&2 ;;
esac

# Motion IO resolves relative paths against its own working directory, which is
# not necessarily this shell's — always hand it absolute paths.
events=$(cd "$(dirname "$events")" && printf '%s/%s' "$PWD" "$(basename "$events")")
mkdir -p "$outdir"
outdir=$(cd "$outdir" && pwd)
log="$outdir/rebelle.log"
pattern=${REBELLE_OUT_PATTERN:-"$outdir/frame_####.png"}

: > "$log"
"$app" -batch-json "$events" -batch-out-rgba_canvas "$pattern" -no-gui "$@" > "$log" 2>&1 &
app_pid=$!
# Kill the app on any exit path, including Ctrl-C, so no stray GUI is left behind.
trap 'kill "$app_pid" 2>/dev/null || true' EXIT

deadline=$((SECONDS + timeout))
done=0
while (( SECONDS < deadline )); do
  # "batch frame end: i/n" — the render is complete when i reaches n.
  # (awk rather than a grep backreference, which POSIX ERE does not define)
  if awk -F'batch frame end: ' 'NF > 1 { split($2, f, "/"); if (f[1] + 0 == f[2] + 0) found = 1 }
       END { exit !found }' "$log"; then done=1; break; fi
  kill -0 "$app_pid" 2>/dev/null || { done=1; break; }
  sleep 1
done

kill "$app_pid" 2>/dev/null || true
wait "$app_pid" 2>/dev/null || true

grep -E '^\[.*(ERROR|Error|error:)' "$log" | sort -u | head -20 >&2 || true

if (( ! done )); then
  cat >&2 <<EOF
timed out after ${timeout}s without a final "batch frame end" line.
Last log lines:
$(grep -vE 'Timer|dock parent|UNSUPPORTED|FPS:' "$log" | tail -5)
A stall before the first "batch frame end" means Motion IO never finished starting up.
Give frame 0 a SET_BRUSH warm-up (a BOOKMARK alone is not enough) and keep
NEW_ARTWORK out of frame 0 — see the Batch section of SKILL.md.
EOF
  exit 1
fi

frames=$(find "$outdir" -maxdepth 1 \( -name '*.png' -o -name '*.exr' -o -name '*.tif' \) | wc -l | tr -d ' ')
echo "rendered $frames file(s) to $outdir"
