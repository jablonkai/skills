#!/usr/bin/env bash
# Launch draw.io desktop with the DevTools port open so drawio-eval.mjs can
# drive it, optionally opening (or creating) a .drawio file.
#
#   bash drawio-start.sh [path/to/file.drawio]
#
# Exit codes: 0 ready, 2 bad usage / app missing, 3 draw.io already running
# without the port (the user has to quit it first), 4 timed out.
# Env: DRAWIO_PORT (default 9338), DRAWIO_APP (default /Applications/draw.io.app).
set -euo pipefail

PORT="${DRAWIO_PORT:-9338}"
APP="${DRAWIO_APP:-/Applications/draw.io.app}"
BIN="$APP/Contents/MacOS/draw.io"
HERE="$(cd "$(dirname "$0")" && pwd)"

if [[ ! -x "$BIN" ]]; then
  echo "draw.io not found at $APP — install it (brew install --cask drawio) or set DRAWIO_APP" >&2
  exit 2
fi

# Already listening: nothing to launch. draw.io will not open a file handed to
# it from outside while it runs, so a different file must be opened by the user.
if curl -fs "http://127.0.0.1:$PORT/json/version" >/dev/null 2>&1; then
  node "$HERE/drawio-eval.mjs" --port "$PORT" --ping
  if [[ $# -gt 0 ]]; then
    echo "note: draw.io was already running; if $(basename "$1") is not in the windows above, ask the user to open it with File > Open" >&2
  fi
  exit 0
fi

if pgrep -f "$BIN" >/dev/null 2>&1; then
  echo "draw.io is running without the control port. Ask the user to save their work and quit draw.io (Cmd+Q), then run this again." >&2
  exit 3
fi

args=(--remote-debugging-port="$PORT" --disable-update)
if [[ $# -gt 0 ]]; then
  file="$1"
  case "$file" in
    *.drawio|*.xml) ;;
    *) echo "expected a .drawio file, got: $file" >&2; exit 2 ;;
  esac
  mkdir -p "$(dirname "$file")"
  file="$(cd "$(dirname "$file")" && pwd)/$(basename "$file")"
  if [[ ! -e "$file" ]]; then
    # A file passed on the command line counts as user intent, so draw.io
    # lets the window save back to it. Start from an empty one-page diagram.
    printf '%s\n' '<mxfile><diagram id="page-1" name="Page-1"><mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/></root></mxGraphModel></diagram></mxfile>' > "$file"
  fi
  args+=("$file")
fi

nohup "$BIN" "${args[@]}" >/dev/null 2>&1 &

for _ in $(seq 1 60); do
  if out="$(node "$HERE/drawio-eval.mjs" --port "$PORT" --ping 2>/dev/null)"; then
    echo "$out"
    exit 0
  fi
  sleep 0.5
done
echo "draw.io did not answer on port $PORT within 30s" >&2
exit 4
