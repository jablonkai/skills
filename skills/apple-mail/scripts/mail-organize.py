#!/usr/bin/env python3
"""Move, archive, flag or mark messages read/unread in bulk. Never deletes, never sends.

  mail-organize.py archive --newsletter --before 90d --mailbox "Google/INBOX"          # preview
  mail-organize.py archive --newsletter --before 90d --mailbox "Google/INBOX" --yes    # do it
  mail-organize.py move --dest "On My Mac/Receipts" --from shop@x.test --yes
  mail-organize.py flag --color red --from boss@corp.test --since 7d --yes
  mail-organize.py read --mailbox "Exchange/Inbox" --before 30d --unread --yes
  mail-organize.py unflag --ids-from hits.json --yes

Without --yes it only prints the matched set (count, sample, target) and exits 0, so run
it once, show the user, then repeat with --yes. archive = move to the source account's
Archive mailbox (localized names found automatically) or --dest. Every change is read back:
moved messages are looked up by Message-ID in the target, flags re-read (exit 4 on a mismatch).
"""
import argparse
import time

import mail_lib as L

COLORS = {"red": 0, "orange": 1, "yellow": 2, "green": 3, "blue": 4, "purple": 5, "gray": 6, "grey": 6}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["move", "archive", "flag", "unflag", "read", "unread"])
    ap.add_argument("--to-mailbox", "--dest", dest="dest", help="target mailbox for move/archive")
    ap.add_argument("--color", choices=sorted(COLORS), help="flag colour")
    ap.add_argument("--yes", action="store_true", help="apply (otherwise preview only)")
    L.add_filter_args(ap)
    a = ap.parse_args()
    L.DEFAULT_TIMEOUT = a.timeout
    if a.action == "move" and not a.dest:
        L.die("move needs --dest 'Account/Mailbox' (--to is the recipient filter)", 2)
    rows = L.search(a)
    mbs = L.mailboxes()

    plan = {}
    if a.action in ("move", "archive"):
        for r in rows:
            src_acct = r["mailbox"].split("/", 1)[0] if not r["mailbox"].startswith(L.LOCAL + "/") else L.LOCAL
            if a.dest:
                dest = L.resolve_mailbox(a.dest, mbs)["key"]
            else:
                arch = L.archive_mailbox(src_acct, mbs)
                if not arch:
                    L.die(f"no Archive mailbox in {src_acct!r}; pass --dest 'Account/Mailbox'", 2)
                dest = arch["key"]
            if r["mailbox"] == dest:
                continue
            plan.setdefault(dest, []).append(r)
    else:
        plan[None] = rows

    total = sum(len(v) for v in plan.values())
    preview = {"action": a.action, "matched": total,
               "targets": {k or "(in place)": len(v) for k, v in plan.items()},
               "sample": [{k: r.get(k) for k in ("date", "from", "subject", "mailbox", "ref")}
                          for v in plan.values() for r in v][:15]}
    if not a.yes or not total:
        preview["applied"] = False
        if total:
            preview["next"] = "re-run with --yes to apply"
        L.dump(preview)
        return

    problems = []
    for dest, items in plan.items():
        res = L.jxa("organize", {"refs": [r["ref"] for r in items], "action": "move" if dest else a.action,
                                 "target": dest, "color": COLORS.get(a.color)}, timeout=a.timeout)
        problems += [f"{x['ref']}: {x.get('error')}" for x in res if not x["ok"]]
    # Read back.
    time.sleep(1.5)
    if a.action in ("move", "archive"):
        for dest, items in plan.items():
            want = {r["messageId"] for r in items if r.get("messageId")}
            got = set()
            for _ in range(5):
                got = {m["messageId"] for m in L.jxa("fetch", {"keys": [dest]})["messages"]}
                if want <= got:
                    break
                time.sleep(2)
            missing = want - got
            if missing:
                problems.append(f"{len(missing)} message(s) not found in {dest} after the move")
            srcs = sorted({r["mailbox"] for r in items})
            left = {m["messageId"] for m in L.jxa("fetch", {"keys": srcs})["messages"]} & want
            if left and not any(("All Mail" in s or "Összes" in s) for s in srcs):
                problems.append(f"{len(left)} message(s) still in the source mailbox")
    else:
        attr, val = {"flag": ("flagged", True), "unflag": ("flagged", False),
                     "read": ("read", True), "unread": ("read", False)}[a.action]
        det = L.jxa("details", {"refs": [r["ref"] for r in rows]})
        bad = [d["ref"] for d in det if d.get("error") or d.get(attr) != val]
        if a.color and a.action == "flag":
            bad += [d["ref"] for d in det if not d.get("error") and d.get("flagIndex") != COLORS[a.color]]
        if bad:
            problems.append(f"{len(bad)} message(s) not {a.action}ged: {bad[:5]}")
    preview.update({"applied": True, "readback": {"ok": not problems, "problems": problems}})
    preview.pop("sample")
    L.dump(preview)
    if problems:
        raise SystemExit(4)


if __name__ == "__main__":
    main()
