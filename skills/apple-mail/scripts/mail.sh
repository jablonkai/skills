#!/usr/bin/env bash
# Check the Apple Mail setup, list mailboxes, or dispatch to a helper script.
#
#   bash mail.sh check        macOS + Mail version, Automation permission, accounts,
#                             Full Disk Access / Envelope Index status (optional fast path)
#   bash mail.sh mailboxes [--counts] [--account NAME]   every mailbox as 'Account/Path'
#   bash mail.sh search|export|draft|organize|verify [args...]   -> mail-<cmd>.py
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)

case "${1:-check}" in
  search | export | draft | organize | verify)
    cmd=$1
    shift
    exec python3 "$here/mail-$cmd.py" "$@"
    ;;
  mailboxes)
    shift
    exec python3 - "$here" "$@" <<'PY'
import argparse, sys
sys.path.insert(0, sys.argv[1])
import mail_lib as L
ap = argparse.ArgumentParser(prog="mail.sh mailboxes")
ap.add_argument("--counts", action="store_true")
ap.add_argument("--account")
a = ap.parse_args(sys.argv[2:])
for m in L.mailboxes(a.account, a.counts):
    extra = ""
    if a.counts:
        extra = f"  ({m['error']})" if "error" in m else f"  {m['count']} msgs, {m['unread']} unread"
    print(m["key"] + extra)
PY
    ;;
  check) ;;
  *)
    echo "usage: mail.sh check | mailboxes | search | export | draft | organize | verify [args...]" >&2
    exit 2
    ;;
esac

if [[ "$(uname)" != "Darwin" ]]; then
  echo "Apple Mail automation needs macOS." >&2
  exit 2
fi
echo "macOS: $(sw_vers -productVersion)"
echo "Mail.app: $(defaults read /System/Applications/Mail.app/Contents/Info.plist CFBundleShortVersionString 2>/dev/null || echo unknown)"
echo "python3: $(python3 -c 'import sys; print(sys.version.split()[0])')"

if ! out=$(python3 - "$here" <<'PY' 2>&1
import sys
sys.path.insert(0, sys.argv[1])
import mail_lib as L
from collections import Counter
mbs = L.mailboxes()
print("automation: allowed")
for acct, n in Counter(m["account"] for m in mbs).items():
    print(f"  {acct}: {n} mailboxes")
st, p = L.index_status()
if st == "ok":
    import sqlite3
    con = L.index_connect()
    n = con.execute("select count(*) from messages where deleted = 0").fetchone()[0]
    print(f"envelope index: readable ({n} messages) -> fast search path on")
elif st == "no-fda":
    print("envelope index: no Full Disk Access -> JXA search only (works; slower on big mailboxes)")
else:
    print("envelope index: not found -> JXA search only")
PY
); then
  echo "$out" | tail -n 3
  echo "automation: DENIED or Mail unavailable (System Settings > Privacy & Security > Automation >"
  echo "  allow this terminal/IDE to control Mail; macOS asks on the first run)"
  exit 3
fi
echo "$out"
