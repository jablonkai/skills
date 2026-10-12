#!/usr/bin/env bash
# Check the Apple Reminders setup, or dispatch to a helper script.
#
#   bash rem.sh check          macOS + Reminders version, EventKit access, the lists with
#                              account, open/overdue counts and which one is the default
#   bash rem.sh list|import|write|verify [args...]   -> rem-<cmd>.py
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)

case "${1:-check}" in
  list | import | write | verify)
    cmd=$1
    shift
    exec python3 "$here/rem-$cmd.py" "$@"
    ;;
  check) ;;
  *)
    echo "usage: rem.sh check | list | import | write | verify [args...]" >&2
    exit 2
    ;;
esac

if [[ "$(uname)" != "Darwin" ]]; then
  echo "Apple Reminders automation needs macOS." >&2
  exit 2
fi
echo "macOS: $(sw_vers -productVersion)"
echo "Reminders.app: $(defaults read /System/Applications/Reminders.app/Contents/Info.plist CFBundleShortVersionString 2>/dev/null || echo unknown)"
echo "python3: $(python3 -c 'import sys; print(sys.version.split()[0])')"
if command -v swiftc >/dev/null; then
  echo "swiftc: yes (the EventKit helper is compiled on first use)"
else
  echo "swiftc: MISSING (xcode-select --install; without it the permission prompt can't appear" \
    "and reads use the slow AppleScript path)"
fi

status=$(python3 - "$here" <<'PY' 2>&1 || true
import sys
sys.path.insert(0, sys.argv[1])
import rem_lib as L
print(L.access())
PY
)
status=${status##*$'\n'}
case "$status" in
  fullAccess) echo "eventkit: fullAccess (fast reads and writes)" ;;
  notDetermined) echo "eventkit: notDetermined (macOS asks on the first read: answer Allow)" ;;
  denied | restricted | writeOnly) echo "eventkit: $status (System Settings > Privacy & Security > Reminders > enable" \
    "this terminal/IDE; until then reads use AppleScript and writes fail)" ;;
  *) echo "eventkit: unknown ($status)" ;;
esac

python3 "$here/rem-list.py" --lists
