#!/usr/bin/env python3
"""Check Mail's state against an expectation, by fresh JXA read-back. Read-only.

  mail-verify.py mailbox --mailbox "On My Mac/Archive" --expect-ids ids.txt [--exact]
  mail-verify.py mailbox --mailbox "Google/INBOX" --absent-ids ids.txt
  mail-verify.py draft --subject "Re: Lease" --to anna@example.com --attach contract.pdf
  mail-verify.py export --dir ~/Invoices

ids files hold one Message-ID per line (with or without <>). `mailbox` reports which
expected messages are present/missing (and, with --exact, unexpected extras) plus their
flag and read state. `draft` finds the newest draft with that subject and checks its
recipients and attachments. `export` re-hashes every file in manifest.json.
Exit 0 when everything matches, 4 when not.
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import mail_lib as L


def ids_file(p):
    return {x.strip().strip("<>") for x in Path(p).read_text(encoding="utf-8").split() if x.strip()}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("mailbox")
    m.add_argument("--mailbox", required=True)
    m.add_argument("--expect-ids")
    m.add_argument("--absent-ids")
    m.add_argument("--exact", action="store_true")
    d = sub.add_parser("draft")
    d.add_argument("--subject", required=True)
    d.add_argument("--to", action="append", default=[])
    d.add_argument("--attach", action="append", default=[])
    e = sub.add_parser("export")
    e.add_argument("--dir", required=True)
    a = ap.parse_args()
    problems, out = [], {}

    if a.cmd == "mailbox":
        key = L.resolve_mailbox(a.mailbox)["key"]
        msgs = L.jxa("fetch", {"keys": [key]})["messages"]
        have = {x["messageId"]: x for x in msgs}
        out = {"mailbox": key, "count": len(msgs)}
        if a.expect_ids:
            want = ids_file(a.expect_ids)
            out["missing"] = sorted(want - have.keys())
            problems += [f"missing {x}" for x in out["missing"]]
            if a.exact:
                out["unexpected"] = sorted(have.keys() - want)
                problems += [f"unexpected {x}" for x in out["unexpected"]]
            out["present"] = [{"messageId": k, "subject": have[k]["subject"], "flagged": have[k]["flagged"],
                               "read": have[k]["read"]} for k in sorted(want & have.keys())]
        if a.absent_ids:
            bad = sorted(ids_file(a.absent_ids) & have.keys())
            out["should_be_absent"] = bad
            problems += [f"still present {x}" for x in bad]
    elif a.cmd == "draft":
        drafts = [mb["key"] for mb in L.mailboxes() if L.fold(mb["path"].rsplit("/", 1)[-1])
                  in ("drafts", "draft", "piszkozatok", "entwürfe", "brouillons", "borradores")]
        hits = [x for x in L.jxa("fetch", {"keys": drafts})["messages"] if x["subject"] == a.subject]
        if not hits:
            problems.append(f"no draft with subject {a.subject!r}")
        else:
            dd = L.jxa("details", {"refs": [max(hits, key=lambda x: x["id"])["ref"]]})[0]
            names = [L.nfc(x["name"]) for x in dd.get("attachments", [])]
            out = {"draft": dd["ref"], "to": dd["to"], "cc": dd["cc"], "attachments": names,
                   "matching_drafts": len(hits)}
            for t in a.to:
                if not any(L.fold(t) in L.fold(x) for x in dd["to"]):
                    problems.append(f"missing To {t}")
            if Counter(Path(x).name for x in a.attach) - Counter(names):
                problems.append(f"attachments {names} lack {a.attach}")
    else:
        root = Path(a.dir).expanduser()
        man = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        n = 0
        for msg in man["messages"]:
            for att in msg["attachments"]:
                n += 1
                p = root / att["file"]
                if not p.is_file():
                    problems.append(f"missing {att['file']}")
                elif hashlib.sha256(p.read_bytes()).hexdigest() != att["sha256"]:
                    problems.append(f"hash mismatch {att['file']}")
        out = {"dir": str(root), "messages": len(man["messages"]), "attachments": n,
               "not_exported": man.get("not_exported", [])}
    out["ok"] = not problems
    out["problems"] = problems
    L.dump(out)
    if problems:
        raise SystemExit(4)


if __name__ == "__main__":
    main()
