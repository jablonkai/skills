#!/usr/bin/env bash
# Locate osxphotos and check the Photos setup, or run osxphotos.
#
#   bash photos.sh --check [--library LIB]   osxphotos, Photos version, readable library, open library,
#                                            permissions; exit 2 if osxphotos is missing
#   bash photos.sh [args...]  run osxphotos with the given arguments
#
# Override the lookup with OSXPHOTOS=/path/to/osxphotos.
set -euo pipefail

find_osxphotos() {
  local candidate
  for candidate in \
    "${OSXPHOTOS:-}" \
    "$(command -v osxphotos 2>/dev/null || true)" \
    "$HOME/.local/bin/osxphotos" \
    /opt/homebrew/bin/osxphotos; do
    if [[ -n "$candidate" && -x "$candidate" ]]; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

if ! BIN=$(find_osxphotos); then
  echo "osxphotos not found." >&2
  echo "Install: uv tool install --python 3.13 osxphotos   (needs Python 3.10-3.14; uv fetches it)" >&2
  echo "Or set OSXPHOTOS=/path/to/osxphotos" >&2
  exit 2
fi

if [[ "${1:-}" != "--check" ]]; then
  exec "$BIN" "$@"
fi

echo "osxphotos: $BIN ($("$BIN" --version 2>/dev/null | sed -n "1s/.*version //p"))"
echo "Photos.app: $(defaults read /System/Applications/Photos.app/Contents/Info.plist CFBundleShortVersionString 2>/dev/null || echo unknown)"
echo "macOS: $(sw_vers -productVersion)"

label="default library"
lib="$HOME/Pictures/Photos Library.photoslibrary"
if [[ "${2:-}" == "--library" && -n "${3:-}" ]]; then
  label="library"
  lib="${3/#\~/$HOME}"
fi
if [[ -d "$lib" ]]; then
  if ls "$lib/database" >/dev/null 2>&1; then
    echo "$label: $lib (readable)"
  else
    echo "$label: $lib (NOT readable: grant Full Disk Access to this terminal/IDE in"
    echo "  System Settings > Privacy & Security > Full Disk Access, then restart it)"
  fi
else
  echo "$label: none at $lib (pass --library PATH; 'osxphotos list' finds libraries)"
fi

pid=$(pgrep -x Photos || true)
if [[ -z "$pid" ]]; then
  echo "open in Photos: (Photos not running; AppleScript writes need it running)"
else
  open_db=$(lsof -Fn -p "$pid" 2>/dev/null | sed -n 's/^n\(.*\)\/database\/Photos\.sqlite$/\1/p' | head -n 1)
  echo "open in Photos: ${open_db:-unknown}"
  if osascript -e 'tell application "Photos" to count albums' >/dev/null 2>&1; then
    echo "automation: allowed"
  else
    echo "automation: DENIED or not yet granted (System Settings > Privacy & Security > Automation > Photos)"
  fi
fi
