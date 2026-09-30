#!/usr/bin/env bash
# Checks and read-only queries around Final Cut Pro automation.
#
#   bash fcp.sh --check            app, version, FCPXML versions, running state, permissions
#   bash fcp.sh --projects         library / event / project / duration (JSON lines)
#   bash fcp.sh --templates [RE]   installed title and transition templates with their uid
#   bash fcp.sh --dialogs          open FCP windows and dialog texts (a blocked import?)
#
# Nothing here writes to FCP or its libraries. The skill never quits FCP; a stuck
# fcp-import.py ends at its --timeout (FCP_TIMEOUT, default 120 s) and leaves FCP as is.
set -euo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
BUNDLE_ID=com.apple.FinalCut

find_app() {
  local app
  app=$(mdfind "kMDItemCFBundleIdentifier == '$BUNDLE_ID'" 2>/dev/null | grep '\.app$' | head -n1 || true)
  if [[ -z "$app" ]]; then
    for app in "/Applications/Final Cut Pro.app" "$HOME/Applications/Final Cut Pro.app"; do
      [[ -d "$app" ]] && break
    done
  fi
  [[ -d "$app" ]] && printf '%s' "$app"
}

check() {
  local app version versions latest out rc
  if ! app=$(find_app); then
    echo "Final Cut Pro not found (bundle id $BUNDLE_ID) — install it from the App Store" >&2
    exit 2
  fi
  version=$(defaults read "$app/Contents/Info" CFBundleShortVersionString 2>/dev/null || echo "?")
  versions=$(find "$app/Contents/Frameworks/Interchange.framework/Versions/A/Resources" \
    -name 'FCPXMLv*.dtd' 2>/dev/null | sed -E 's/.*FCPXMLv([0-9]+)_([0-9]+)\.dtd/\1.\2/' |
    sort -t. -k1,1n -k2,2n | tr '\n' ' ')
  latest=$(printf '%s' "$versions" | awk '{print $NF}')
  echo "app: $app"
  echo "version: $version"
  echo "fcpxml_versions: $versions"
  echo "fcpxml_write: $latest"
  for tool in ffprobe xmllint; do
    if command -v "$tool" >/dev/null; then echo "$tool: $(command -v "$tool")"
    else echo "$tool: MISSING$([[ $tool == ffprobe ]] && echo ' (brew install ffmpeg)')"; fi
  done
  if ! pgrep -x "Final Cut Pro" >/dev/null; then
    echo "running: no (fcp-import.py launches it; the AppleScript checks need it running)"
    return 0
  fi
  echo "running: yes"
  set +e
  out=$(osascript -e 'with timeout of 30 seconds' \
    -e "tell application id \"$BUNDLE_ID\" to get name of every library" -e 'end timeout' 2>&1)
  rc=$?
  set -e
  if [[ $rc -eq 0 ]]; then
    echo "automation: ok"
    echo "libraries: ${out:-(none open)}"
  elif [[ "$out" == *"-1743"* ]]; then
    echo "automation: DENIED — System Settings ▸ Privacy & Security ▸ Automation ▸ allow the terminal to control Final Cut Pro"
  else
    echo "automation: ERROR $out"
  fi
  set +e
  out=$(osascript -e 'tell application "System Events" to tell process "Final Cut Pro" to count windows' 2>&1)
  rc=$?
  set -e
  if [[ $rc -eq 0 ]]; then echo "accessibility: ok"
  else echo "accessibility: DENIED — import dialogs can't be watched (System Settings ▸ Privacy & Security ▸ Accessibility ▸ the terminal)"; fi
}

projects() {
  python3 - "$HERE" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
from fcpxml_common import FcpError, emit, list_projects
try:
    for p in list_projects():
        emit(p)
except FcpError as e:
    emit({"ok": False, "error": str(e)})
    sys.exit(1)
PY
}

templates() {
  local app re=${1:-.}
  app=$(find_app) || { echo "Final Cut Pro not found" >&2; exit 2; }
  local base="$app/Contents/PlugIns/MediaProviders/MotionEffect.fxp/Contents/Resources"
  for root in Templates.localized PETemplates.localized; do
    [[ -d "$base/$root" ]] || continue
    (cd "$base/$root" && find Titles.localized Transitions.localized \( -name '*.moti' -o -name '*.motr' \) 2>/dev/null) |
      while IFS= read -r rel; do
        name=$(basename "$rel"); name=${name%.*}
        kind=title; [[ $rel == Transitions.localized/* ]] && kind=transition
        printf '%s\t%s\t.../%s\n' "$kind" "$name" "$rel"
      done
  done | sort -u | grep -i -E -- "$re" || true
  echo "built in (no template file): transition	Cross Dissolve	FxPlug:4731E73A-8DAC-4113-9A30-AE85B1761265" >&2
}

dialogs() {
  osascript <<'OSA'
tell application "System Events"
  if not (exists process "Final Cut Pro") then return "not running"
  tell process "Final Cut Pro"
    set out to ""
    repeat with w in windows
      set out to out & "window: " & (name of w) & linefeed
      try
        repeat with s in (value of every static text of w)
          set out to out & "  " & s & linefeed
        end repeat
      end try
      try
        repeat with s in (value of every static text of sheet 1 of w)
          set out to out & "  sheet: " & s & linefeed
        end repeat
      end try
    end repeat
    return out
  end tell
end tell
OSA
}

case "${1:-}" in
  --check) check ;;
  --projects) projects ;;
  --templates) templates "${2:-}" ;;
  --dialogs) dialogs ;;
  *) sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'; exit 2 ;;
esac
