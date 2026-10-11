#!/usr/bin/env bash
# Check the Apple Contacts setup, or dispatch to a helper script.
#
#   bash contacts.sh check          macOS + Contacts version, framework access, the
#                                   accounts with counts and the groups
#   bash contacts.sh search|export|audit|write|verify [args...]   -> ct-<cmd>.py
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)

case "${1:-check}" in
  search | export | audit | write | verify)
    cmd=$1
    shift
    exec python3 "$here/ct-$cmd.py" "$@"
    ;;
  check) ;;
  *)
    echo "usage: contacts.sh check | search | export | audit | write | verify [args...]" >&2
    exit 2
    ;;
esac

if [[ "$(uname)" != "Darwin" ]]; then
  echo "Apple Contacts automation needs macOS." >&2
  exit 2
fi
echo "macOS: $(sw_vers -productVersion)"
echo "Contacts.app: $(defaults read /System/Applications/Contacts.app/Contents/Info.plist CFBundleShortVersionString 2>/dev/null || echo unknown)"
echo "python3: $(python3 -c 'import sys; print(sys.version.split()[0])')"
if command -v swiftc >/dev/null; then
  echo "swiftc: yes (the Contacts helper is compiled on first use)"
else
  echo "swiftc: MISSING (xcode-select --install; without it reads use AppleScript and writes are unavailable)"
fi

status=$(python3 - "$here" <<'PY' 2>&1 || true
import sys
sys.path.insert(0, sys.argv[1])
import ct_lib as L
print(L.access())
PY
)
status=${status##*$'\n'}
case "$status" in
  authorized) echo "contacts: authorized (framework reads and writes)" ;;
  limited) echo "contacts: limited (only the contacts shared with this app are visible)" ;;
  notDetermined) echo "contacts: notDetermined (macOS asks on the first read: answer Allow)" ;;
  denied | restricted) echo "contacts: $status (System Settings > Privacy & Security > Contacts > enable" \
    "this terminal/IDE; until then reads use AppleScript and writes fail)" ;;
  *) echo "contacts: $status" ;;
esac

python3 "$here/ct-search.py" --accounts
echo
python3 "$here/ct-search.py" --groups
