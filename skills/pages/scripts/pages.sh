#!/usr/bin/env bash
# Entry point for checks and housekeeping around Apple Pages automation.
#
#   bash pages.sh --check            app path, version, Automation permission, blockers
#   bash pages.sh --templates [RE]   template id <TAB> localized name (filter by RE)
#   bash pages.sh --dialog           is a modal Pages alert blocking scripting? screenshot it
#   bash pages.sh --close PATH...    close these documents in Pages without saving
#   bash pages.sh --close-leftovers  close documents a killed script run left open
#
# Stop path: a stuck call ends at its timeout (PAGES_TIMEOUT, default 300 s); then
# --close-leftovers closes only what the scripts opened. Pages itself is never quit.
set -euo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
BUNDLE_ID=com.apple.Pages

find_app() {
  local app
  app=$(mdfind "kMDItemCFBundleIdentifier == '$BUNDLE_ID'" 2>/dev/null | grep '\.app$' | head -n1 || true)
  if [[ -z "$app" ]]; then
    for app in /Applications/Pages*.app "$HOME"/Applications/Pages*.app; do
      [[ -d "$app" ]] && break
    done
  fi
  [[ -d "$app" ]] && printf '%s' "$app"
}

check() {
  local app version out rc
  if ! app=$(find_app); then
    echo "Pages not found — install it from the App Store (bundle id $BUNDLE_ID)" >&2
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
      *-1712*) echo "automation: NO ANSWER"; python3 "$HERE/pages_osa.py" --dialog || true ;;
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
  --templates)
    osascript -l JavaScript -e "
      const P = Application('$BUNDLE_ID');
      P.templates().map(t => t.id() + '\t' + t.name()).join('\n');" |
      grep -iE -- "${2:-.}" || true
    ;;
  --dialog) python3 "$HERE/pages_osa.py" --dialog ;;
  --close)
    shift
    [[ $# -gt 0 ]] || { echo "usage: pages.sh --close PATH..." >&2; exit 2; }
    paths=()
    for p in "$@"; do paths+=("$(cd "$(dirname "$p")" && pwd -P)/$(basename "$p")"); done
    osascript "$HERE/pages_ops.applescript" close "${paths[@]}"
    ;;
  --close-leftovers) python3 "$HERE/pages_osa.py" --close-leftovers ;;
  *)
    sed -n '2,11p' "$0" >&2
    exit 2
    ;;
esac
