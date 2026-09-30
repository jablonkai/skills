#!/usr/bin/env bash
# Entry point for checks and housekeeping around Apple Keynote automation.
#
#   bash keynote.sh --check            app path, version, Automation permission, blockers
#   bash keynote.sh --themes [RE]      theme id <TAB> localized name (filter by RE)
#   bash keynote.sh --layouts THEME    index, English name, localized name, placeholders
#   bash keynote.sh --dialog           is a modal Keynote alert blocking scripting? screenshot it
#   bash keynote.sh --close PATH...    close these decks in Keynote without saving
#   bash keynote.sh --close-leftovers  close decks a killed script run left open
#
# Stop path: a stuck call ends at its timeout (KEYNOTE_TIMEOUT, default 300 s); then
# --close-leftovers closes only what the scripts opened. Keynote itself is never quit.
set -euo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
BUNDLE_ID=com.apple.Keynote

find_app() {
  local app
  app=$(mdfind "kMDItemCFBundleIdentifier == '$BUNDLE_ID'" 2>/dev/null | grep '\.app$' | head -n1 || true)
  if [[ -z "$app" ]]; then
    for app in /Applications/Keynote*.app "$HOME"/Applications/Keynote*.app; do
      [[ -d "$app" ]] && break
    done
  fi
  [[ -d "$app" ]] && printf '%s' "$app"
}

check() {
  local app version out rc
  if ! app=$(find_app); then
    echo "Keynote not found — install it from the App Store (bundle id $BUNDLE_ID)" >&2
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
      *-1712*) echo "automation: NO ANSWER"; python3 "$HERE/keynote_osa.py" --dialog || true ;;
      *) echo "automation: ERROR $out" ;;
    esac
    exit 2
  fi
  echo "automation: ok"
  echo "open documents: $out"
  if command -v pdftotext >/dev/null; then
    echo "pdf text: pdftotext"
  else
    echo "pdf text: PDFKit (pdftotext not installed; not needed)"
  fi
}

case "${1:-}" in
  --check) check ;;
  --themes)
    osascript -l JavaScript -e "
      const K = Application('$BUNDLE_ID');
      K.themes().map(t => t.id() + '\t' + t.name()).join('\n');" |
      grep -iE -- "${2:-.}" || true
    ;;
  --layouts)
    [[ $# -ge 2 ]] || { echo "usage: keynote.sh --layouts THEME_ID_OR_NAME" >&2; exit 2; }
    python3 "$HERE/keynote_osa.py" --layouts "$2"
    ;;
  --dialog) python3 "$HERE/keynote_osa.py" --dialog ;;
  --close)
    shift
    [[ $# -gt 0 ]] || { echo "usage: keynote.sh --close PATH..." >&2; exit 2; }
    paths=()
    for p in "$@"; do paths+=("$(cd "$(dirname "$p")" && pwd -P)/$(basename "$p")"); done
    osascript "$HERE/keynote_ops.applescript" close "${paths[@]}"
    ;;
  --close-leftovers) python3 "$HERE/keynote_osa.py" --close-leftovers ;;
  *)
    sed -n '2,12p' "$0" >&2
    exit 2
    ;;
esac
