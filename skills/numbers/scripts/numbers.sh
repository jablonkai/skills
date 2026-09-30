#!/usr/bin/env bash
# Entry point for checks and housekeeping around Apple Numbers automation.
#
#   bash numbers.sh --check            app path, version, Automation permission, locale
#   bash numbers.sh --dialog           is a modal Numbers alert blocking scripting? screenshot it
#   bash numbers.sh --close PATH...    close these documents in Numbers without saving
#   bash numbers.sh --close-leftovers  close documents a killed script run left open
#
# Stop path: a stuck call ends at its timeout (NUMBERS_TIMEOUT, default 300 s); then
# --close-leftovers closes only what the scripts opened. Numbers itself is never quit.
set -euo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
BUNDLE_ID=com.apple.Numbers

find_app() {
  local app
  app=$(mdfind "kMDItemCFBundleIdentifier == '$BUNDLE_ID'" 2>/dev/null | grep '\.app$' | head -n1 || true)
  if [[ -z "$app" ]]; then
    for app in /Applications/Numbers*.app "$HOME"/Applications/Numbers*.app; do
      [[ -d "$app" ]] && break
    done
  fi
  [[ -d "$app" ]] && printf '%s' "$app"
}

check() {
  local app version out rc
  if ! app=$(find_app); then
    echo "Numbers not found — install it from the App Store (bundle id $BUNDLE_ID)" >&2
    exit 2
  fi
  version=$(defaults read "$app/Contents/Info" CFBundleShortVersionString 2>/dev/null || echo "?")
  echo "app: $app"
  echo "version: $version"
  set +e
  out=$(osascript -e 'with timeout of 20 seconds' \
    -e "tell application id \"$BUNDLE_ID\" to count documents" -e 'end timeout' 2>&1)
  rc=$?
  set -e
  if [[ $rc -ne 0 ]]; then
    case "$out" in
      *-1743*) echo "automation: DENIED — allow it in System Settings > Privacy & Security > Automation" ;;
      *-1712*) echo "automation: NO ANSWER"; python3 "$HERE/numbers_osa.py" --dialog || true ;;
      *) echo "automation: ERROR $out" ;;
    esac
    exit 2
  fi
  echo "automation: ok"
  echo "open documents: $out"
  python3 "$HERE/numbers_osa.py" --locale
}

case "${1:-}" in
  --check) check ;;
  --dialog) python3 "$HERE/numbers_osa.py" --dialog ;;
  --close)
    shift
    [[ $# -gt 0 ]] || { echo "usage: numbers.sh --close PATH..." >&2; exit 2; }
    python3 "$HERE/numbers_osa.py" --close "$@"
    ;;
  --close-leftovers) python3 "$HERE/numbers_osa.py" --close-leftovers ;;
  *)
    sed -n '2,9p' "$0" >&2
    exit 2
    ;;
esac
