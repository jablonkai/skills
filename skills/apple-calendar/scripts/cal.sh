#!/usr/bin/env bash
# Check the Apple Calendar setup, or dispatch to a helper script.
#
#   bash cal.sh check          macOS + Calendar version, EventKit access, Automation
#                              permission, the calendars with type and writability
#   bash cal.sh list|free|write|ics|verify [args...]   -> cal-<cmd>.py
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)

case "${1:-check}" in
  list | free | write | ics | verify)
    cmd=$1
    shift
    exec python3 "$here/cal-$cmd.py" "$@"
    ;;
  check) ;;
  *)
    echo "usage: cal.sh check | list | free | write | ics | verify [args...]" >&2
    exit 2
    ;;
esac

if [[ "$(uname)" != "Darwin" ]]; then
  echo "Apple Calendar automation needs macOS." >&2
  exit 2
fi
echo "macOS: $(sw_vers -productVersion)"
echo "Calendar.app: $(defaults read /System/Applications/Calendar.app/Contents/Info.plist CFBundleShortVersionString 2>/dev/null || echo unknown)"
echo "python3: $(python3 -c 'import sys; print(sys.version.split()[0])')"
if command -v swiftc >/dev/null; then
  echo "swiftc: yes (the EventKit helper is compiled on first use)"
else
  echo "swiftc: MISSING (xcode-select --install; without it reads use the slow AppleScript path)"
fi

status=$(python3 - "$here" <<'PY' 2>&1 || true
import sys
sys.path.insert(0, sys.argv[1])
import cal_lib as L
print(L.access())
PY
)
status=${status##*$'\n'}
case "$status" in
  fullAccess) echo "eventkit: fullAccess (fast reads and writes)" ;;
  writeOnly) echo "eventkit: writeOnly (can add events but not read them: turn on Full Access for this" \
    "terminal/IDE in System Settings > Privacy & Security > Calendars)" ;;
  notDetermined) echo "eventkit: notDetermined (macOS asks on the first read: answer Allow Full Access)" ;;
  denied | restricted) echo "eventkit: $status (System Settings > Privacy & Security > Calendars > enable" \
    "this terminal/IDE; until then reads use AppleScript and writes fail)" ;;
  *) echo "eventkit: unknown ($status)" ;;
esac

python3 "$here/cal-list.py" --calendars
