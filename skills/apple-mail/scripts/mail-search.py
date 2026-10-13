#!/usr/bin/env python3
"""Search Apple Mail and summarise the hits. Read-only.

  mail-search.py --from anna@example.com --since 30d
  mail-search.py --subject invoice --has-attachment --mailbox "Google/INBOX"
  mail-search.py --newsletter --before 90d --mailbox "On My Mac/Newsletters" --json > hits.json
  mail-search.py --unread --account Exchange --since today --limit 20
  mail-search.py --from boss@corp.test --to me@corp.test --format csv

Prints a table (date, from, subject, mailbox, ref) or JSON/CSV. The ref
("Account/Mailbox#id") is what mail-export.py, mail-draft.py --reply-to and
mail-organize.py --id take; `--json` output can be passed back with --ids-from.
Trash, Junk and Spam are skipped unless --include-trash. Uses the Envelope Index when
Full Disk Access allows (milliseconds), else JXA bulk reads (seconds per mailbox).
"""
import argparse
import csv
import sys
from collections import Counter

import mail_lib as L


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    L.add_filter_args(ap)
    ap.add_argument("--format", choices=["table", "json", "csv"], default="table")
    ap.add_argument("--json", action="store_const", const="json", dest="format")
    ap.add_argument("--count-by", choices=["sender", "mailbox", "day"],
                    help="summarise counts instead of listing messages")
    a = ap.parse_args()
    L.DEFAULT_TIMEOUT = a.timeout
    rows = L.search(a)

    if a.count_by:
        key = {"sender": lambda r: r["from"], "mailbox": lambda r: r["mailbox"],
               "day": lambda r: (r["date"] or "")[:10]}[a.count_by]
        c = Counter(key(r) for r in rows)
        if a.format == "json":
            L.dump({"total": len(rows), "counts": c.most_common()})
        else:
            for k, n in c.most_common():
                print(f"{n:6}  {k}")
            print(f"{len(rows):6}  total")
        return
    if a.format == "json":
        L.dump({"count": len(rows), "messages": rows})
        return
    if a.format == "csv":
        w = csv.writer(sys.stdout)
        w.writerow(["date", "from", "subject", "mailbox", "read", "flagged", "ref"])
        for r in rows:
            w.writerow([r["date"], r["from"], r["subject"], r["mailbox"], r.get("read"),
                        r.get("flagged"), r["ref"]])
        return
    for r in rows:
        flags = ("F" if r.get("flagged") else " ") + (" " if r.get("read", True) else "U")
        print(f"{(r['date'] or '')[:16].replace('T', ' ')} {flags} {r['from'][:38]:38}  "
              f"{(r['subject'] or '')[:60]:60}  {r['mailbox']}  {r['ref'].rsplit('#', 1)[1]}")
    print(f"{len(rows)} message(s)" + (f" via {rows[0]['engine']}" if rows else ""))


if __name__ == "__main__":
    main()
