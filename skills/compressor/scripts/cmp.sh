#!/usr/bin/env bash
# Locate Apple Compressor's CLI and run it.
#
#   bash cmp.sh --check        print app version, CLI path, settings folders, ffprobe; exit 2 if missing
#   bash cmp.sh --status ID    one-shot JSON status of a batch (-monitor -once)
#   bash cmp.sh --kill ID      cancel a batch (Compressor deletes its partial outputs)
#   bash cmp.sh [args...]      run the Compressor binary with the given arguments
#
# Override the app location with COMPRESSOR_APP=/path/to/Compressor.app.
set -euo pipefail

APP="${COMPRESSOR_APP:-/Applications/Compressor.app}"
BIN="$APP/Contents/MacOS/Compressor"
USER_SETTINGS="$HOME/Library/Application Support/Compressor/Settings"

if [[ ! -x "$BIN" ]]; then
  echo "Compressor not found at $APP." >&2
  echo "Install it from the Mac App Store, or set COMPRESSOR_APP=/path/to/Compressor.app" >&2
  exit 2
fi

case "${1:-}" in
  --check)
    version=$(defaults read "$APP/Contents/Info" CFBundleShortVersionString 2>/dev/null || echo unknown)
    builtin=$(find "$APP/Contents" -type d -name BuiltInSettings -print -quit 2>/dev/null || true)
    echo "app: $APP"
    echo "version: $version"
    echo "cli: $BIN"
    if [[ -n "$builtin" ]]; then
      echo "built-in settings: $(find "$builtin" -type f \( -name '*.compressorsetting' -o -name '*.cmprstng' -o -name '*.setting' \) | wc -l | tr -d ' ')"
    else
      echo "built-in settings: NOT FOUND (layout changed?)"
    fi
    if [[ -d "$USER_SETTINGS" ]]; then
      echo "custom settings: $(find "$USER_SETTINGS" -type f -name '*.compressorsetting' | wc -l | tr -d ' ') in $USER_SETTINGS"
    else
      echo "custom settings: none yet ($USER_SETTINGS does not exist)"
    fi
    if command -v ffprobe >/dev/null 2>&1; then
      echo "ffprobe: $(command -v ffprobe)"
    else
      echo "ffprobe: MISSING (brew install ffmpeg) — needed for cmp-verify.py"
    fi
    exit 0
    ;;
  --status)
    exec "$BIN" -monitor -batchid "${2:?batch id}" -outputformat json -once 2>/dev/null
    ;;
  --kill)
    exec "$BIN" -kill -batchid "${2:?batch id}"
    ;;
esac

exec "$BIN" "$@"
