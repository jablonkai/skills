#!/usr/bin/env bash
# Check the Apple Notes setup, or dispatch to a helper script.
#
#   bash notes.sh check          macOS + Notes version, Automation permission, accounts and
#                                folders with note counts, Full Disk Access (optional)
#   bash notes.sh search|export|write|verify [args...]   -> nt-<cmd>.py
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)

case "${1:-check}" in
  search | export | write | verify)
    cmd=$1
    shift
    exec python3 "$here/nt-$cmd.py" "$@"
    ;;
  check) ;;
  *)
    echo "usage: notes.sh check | search | export | write | verify [args...]" >&2
    exit 2
    ;;
esac

if [[ "$(uname)" != "Darwin" ]]; then
  echo "Apple Notes automation needs macOS." >&2
  exit 2
fi
echo "macOS: $(sw_vers -productVersion)"
echo "Notes.app: $(defaults read /System/Applications/Notes.app/Contents/Info.plist CFBundleShortVersionString 2>/dev/null || echo unknown)"
echo "python3: $(python3 -c 'import sys; print(sys.version.split()[0])')"

if ! out=$(python3 - "$here" <<'PY' 2>&1
import sys
sys.path.insert(0, sys.argv[1])
import notes_lib as L
from collections import Counter
fs = L.folders()
counts = Counter(n["folderId"] for n in L.jxa("list_notes", {"folderIds": [f["id"] for f in fs], "text": False}))
print("automation: allowed")
for f in fs:
    print(f"  {f['path']}: {counts.get(f['id'], 0)} notes")
PY
); then
  echo "$out" | tail -n 3
  echo "automation: DENIED or Notes unavailable (System Settings > Privacy & Security > Automation >"
  echo "  allow this terminal/IDE to control Notes; macOS asks on the first run)"
  exit 3
fi
echo "$out"

if ls "$HOME/Library/Group Containers/group.com.apple.notes/" >/dev/null 2>&1; then
  echo "full disk access: yes (not needed; the scripts use AppleScript only)"
else
  echo "full disk access: no (fine: the scripts use AppleScript only)"
fi
