#!/usr/bin/env python3
"""Create a draft (new message or reply) with attachments and leave it in Drafts.

This skill has no send capability: the draft is saved and closed, and the user sends it
from Mail. Every draft is read back from the Drafts mailbox (exit 4 on a mismatch).

  mail-draft.py --to anna@example.com --subject "Lease" --body "Hi Anna, ..." --attach ~/contract.pdf
  mail-draft.py --reply-to "Google/[Gmail]/All Mail#49674" --body-file reply.txt --attach contract.pdf
  mail-draft.py --reply-to REF --reply-all --body "Thanks all."
  mail-draft.py --to a@x.test --cc b@x.test --subject S --body B --from "me@work.example" --dry-run

--reply-to takes a ref from mail-search.py. Mail's reply sets the recipients (Reply-To or
sender; --reply-all adds the rest minus your own addresses), "Re: <subject>" (not doubled)
and the In-Reply-To/References threading headers; the new text goes on top with the
quoted original below. --from picks the sending account by address (default for a reply:
the account that holds the original).
"""
import argparse
import time
from collections import Counter
from pathlib import Path

import mail_lib as L


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--reply-to", help="message ref to reply to")
    ap.add_argument("--reply-all", action="store_true")
    ap.add_argument("--to", action="append", default=[])
    ap.add_argument("--cc", action="append", default=[])
    ap.add_argument("--bcc", action="append", default=[])
    ap.add_argument("--subject")
    ap.add_argument("--body", default="")
    ap.add_argument("--body-file")
    ap.add_argument("--attach", action="append", default=[], help="file to attach (repeatable)")
    ap.add_argument("--from", dest="sender", help="sender address, e.g. 'Name <me@x.test>'")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--timeout", type=int, default=120)
    a = ap.parse_args()

    body = Path(a.body_file).expanduser().read_text(encoding="utf-8") if a.body_file else a.body
    files = []
    for f in a.attach:
        p = Path(f).expanduser().resolve()
        if not p.is_file():
            L.die(f"attachment not found: {p}", 2)
        files.append(str(p))
    if not a.reply_to and not (a.to and a.subject is not None):
        L.die("a new draft needs --to and --subject (or use --reply-to REF)", 2)
    if a.reply_to:
        L.split_ref(a.reply_to)
    payload = {"replyTo": a.reply_to, "replyAll": a.reply_all, "to": a.to, "cc": a.cc, "bcc": a.bcc,
               "subject": a.subject, "body": body, "attachments": files, "sender": a.sender}
    if a.dry_run:
        L.dump({"dry_run": True, **payload})
        return

    start = time.time()
    made = L.jxa("draft", payload, timeout=a.timeout)

    # Read back: the newest draft with this subject, in any account's Drafts.
    drafts = [m for m in L.mailboxes() if L.fold(m["path"].rsplit("/", 1)[-1])
              in ("drafts", "draft", "piszkozatok", "entwürfe", "brouillons", "borradores")]
    found = None
    for _ in range(10):
        res = L.jxa("fetch", {"keys": [m["key"] for m in drafts],
                              "since": None})["messages"]
        cands = [r for r in res if r["subject"] == made["subject"]]
        if cands:
            found = max(cands, key=lambda r: r["id"])
            break
        time.sleep(1.5)
    if not found:
        L.die(f"draft {made['subject']!r} not found in Drafts after saving ({drafts and drafts[0]['key']})", 4)
    d = L.jxa("details", {"refs": [found["ref"]], "content": True})[0]
    want_names = sorted(Path(f).name for f in files)
    got_names = sorted(L.nfc(x["name"]) for x in d.get("attachments", []))
    problems = []
    for x in a.to:
        if not any(L.fold(x) in L.fold(t) for t in d["to"]):
            problems.append(f"missing To {x}")
    if a.reply_to and not a.reply_all and not d["to"]:
        problems.append("reply has no recipient")
    head = " ".join(body.split())[:60]
    if head and head not in " ".join((d.get("content") or "").split()):
        problems.append("body text not found in the saved draft")
    if Counter(want_names) - Counter(got_names):
        problems.append(f"attachments {got_names} != {want_names}")
    if made.get("leftoverComposeObjects"):
        L.warn("Mail kept an invisible, unsent compose object for this draft (a Mail scripting quirk). "
               "It is harmless and disappears when Mail quits; the saved draft above is the real one.")
    out = {"draft": found["ref"], "subject": d["subject"], "to": d["to"], "cc": d["cc"],
           "attachments": d.get("attachments", []), "sent": False,
           "readback": {"ok": not problems, "problems": problems},
           "seconds": round(time.time() - start, 1)}
    L.dump(out)
    if problems:
        raise SystemExit(4)


if __name__ == "__main__":
    main()
