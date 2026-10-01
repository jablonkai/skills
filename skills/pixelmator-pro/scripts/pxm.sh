#!/usr/bin/env bash
# Pixelmator Pro runner.
#   pxm.sh check                       app path, version, Automation permission, open docs
#   pxm.sh run FILE|- [--timeout N] [ARGS...]
#                                      run an AppleScript (.applescript/.scpt) or JXA (.js)
#                                      file, or stdin with "-"; default timeout 600 s
#   pxm.sh close-all                   close every open document without saving
# Exit codes: 0 ok, 1 script error, 2 app missing, 3 Automation permission denied,
# 124 timeout (open documents are closed without saving).
set -uo pipefail

APP_ID="com.pixelmatorteam.pixelmator.x"

find_app() {
  local p
  p=$(mdfind "kMDItemCFBundleIdentifier == '$APP_ID'" 2>/dev/null | head -n1)
  [[ -z "$p" && -d "/Applications/Pixelmator Pro.app" ]] && p="/Applications/Pixelmator Pro.app"
  printf '%s' "$p"
}

hint() {  # map well-known Apple Event errors in $1 (stderr text) to a fix
  case "$1" in
    *"-1743"*) echo "pxm: Automation permission denied. System Settings > Privacy & Security > Automation: allow your terminal app to control Pixelmator Pro, then retry." >&2; return 3 ;;
    *"-600"*|*"-609"*) echo "pxm: Pixelmator Pro quit or is not responding. Relaunch it and retry." >&2 ;;
    *"-1712"*) echo "pxm: Apple Event timed out (a modal dialog in Pixelmator Pro may be waiting for a click)." >&2 ;;
  esac
  return 1
}

# Find an alert/dialog window of Pixelmator Pro (System Events, needs Accessibility for
# the terminal), click OK (or Cancel), print its text. Prints nothing when there is none.
dismiss_alert() {
  perl -e 'alarm 8; exec @ARGV' osascript 2>/dev/null <<'AS'
tell application "System Events"
  if not (exists process "Pixelmator Pro") then return ""
  tell process "Pixelmator Pro"
    set ds to (windows whose subrole is "AXDialog")
    if ds is {} then return ""
    set w to item 1 of ds
    set AppleScript's text item delimiters to " "
    set msg to (value of static texts of w) as text
    repeat with b in {"OK", "Cancel", "Don’t Save"}
      if exists button (b as text) of w then
        click button (b as text) of w
        exit repeat
      end if
    end repeat
    return msg
  end tell
end tell
AS
}

close_all() {
  osascript -e 'tell application "Pixelmator Pro" to close every document saving no' >/dev/null 2>&1
}

cmd=${1:-}
shift || true
case "$cmd" in
  check)
    app=$(find_app)
    if [[ -z "$app" ]]; then echo "pxm: Pixelmator Pro not installed" >&2; exit 2; fi
    ver=$(defaults read "$app/Contents/Info" CFBundleShortVersionString 2>/dev/null)
    echo "app: $app"
    echo "version: $ver"
    if out=$(osascript -e 'tell application "Pixelmator Pro" to count documents' 2>&1); then
      echo "automation: ok"
      echo "open documents: $out"
    else
      echo "automation: FAILED ($out)"
      hint "$out"; exit $?
    fi
    ;;
  run)
    file=${1:-}; shift || true
    [[ -z "$file" ]] && { echo "usage: pxm.sh run FILE|- [--timeout N] [ARGS...]" >&2; exit 64; }
    timeout=600
    if [[ "${1:-}" == "--timeout" ]]; then timeout=$2; shift 2; fi
    lang=()
    [[ "$file" == *.js ]] && lang=(-l JavaScript)
    tmp=$(mktemp -d)
    trap 'rm -rf "$tmp"' EXIT
    if [[ "$file" == "-" ]]; then  # background jobs get /dev/null as stdin, so spool it
      file="$tmp/stdin.applescript"
      cat >"$file"
    fi
    osascript ${lang[@]+"${lang[@]}"} "$file" "$@" >"$tmp/out" 2>"$tmp/err" &
    pid=$!
    start=$SECONDS alert="" rc=0
    # Watchdog: an error alert in Pixelmator Pro is app-modal and blocks every later
    # Apple Event, so poll for one, report its text, dismiss it and stop the script.
    while kill -0 "$pid" 2>/dev/null; do
      sleep 1
      a=$(dismiss_alert)
      if [[ -n "$a" ]]; then
        alert=$a
        sleep 3
        kill "$pid" 2>/dev/null
        break
      fi
      if (( SECONDS - start >= timeout )); then
        kill "$pid" 2>/dev/null
        rc=124
        break
      fi
    done
    wait "$pid" 2>/dev/null
    wrc=$?
    if [[ -n "$alert" ]]; then
      echo "pxm: Pixelmator Pro showed an alert (dismissed): $alert" >&2
      close_all
      exit 1
    fi
    if [[ $rc -eq 124 ]]; then
      echo "pxm: timed out after ${timeout}s; closing open documents without saving" >&2
      close_all
      exit 124
    fi
    cat "$tmp/out"
    if [[ $wrc -ne 0 ]]; then
      cat "$tmp/err" >&2
      hint "$(cat "$tmp/err")"; exit $?
    fi
    ;;
  close-all)
    close_all
    ;;
  *)
    sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'
    exit 64
    ;;
esac
