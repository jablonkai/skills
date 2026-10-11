#!/usr/bin/env python3
"""Search notes by text, folder and date. Read-only.

  nt-search.py --text invoice --text 2024            # all terms (case-insensitive), title or body
  nt-search.py --text kestrel --any --text osprey    # any term
  nt-search.py --folder "iCloud/Work" --since 2026-10-01
  nt-search.py --since 2026-10-04 --until 2026-10-11 --date created
  nt-search.py --text recipe --json --limit 50

Matches the note title and its plaintext (accent- and case-insensitive). Skips the
"Recently Deleted" folder unless --include-deleted; locked notes match on title only and
are flagged. Prints title, folder path, modified date and a snippet; --json adds the id
(pass it to nt-export.py / nt-write.py). --since/--until are inclusive local dates.
"""
import argparse
import datetime as dt
import sys
import unicodedata

import notes_lib as L


def fold(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s or "").casefold()
                   if not unicodedata.combining(c))


def local_date(iso):
    return dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone().date()


def snippet(text, terms, width=60):
    flat = " ".join((text or "").replace("￼", " ").split())
    folded = fold(flat)
    pos = min((folded.find(t) for t in terms if folded.find(t) >= 0), default=-1)
    if pos < 0:
        return flat[:width * 2]
    start = max(0, pos - width)
    return ("…" if start else "") + flat[start:pos + width] + ("…" if pos + width < len(flat) else "")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--text", action="append", default=[], help="search term (repeatable)")
    ap.add_argument("--any", action="store_true", help="match any term instead of all")
    ap.add_argument("--title-only", action="store_true")
    ap.add_argument("--folder", help="'Account/Folder' (subfolders included)")
    ap.add_argument("--account")
    ap.add_argument("--since", type=dt.date.fromisoformat)
    ap.add_argument("--until", type=dt.date.fromisoformat)
    ap.add_argument("--date", choices=["modified", "created"], default="modified")
    ap.add_argument("--include-deleted", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--timeout", type=int, default=L.DEFAULT_TIMEOUT)
    a = ap.parse_args()
    L.DEFAULT_TIMEOUT = a.timeout

    fs = L.folders(a.account)
    scope = L.subtree(L.resolve_folder(a.folder, fs), fs) if a.folder else fs
    if not a.include_deleted:
        scope = [f for f in scope if not L.is_deleted_folder(f)]
    paths = {f["id"]: f["path"] for f in fs}
    notes = L.jxa("list_notes", {"folderIds": [f["id"] for f in scope],
                                 "text": bool(a.text) and not a.title_only})
    terms = [fold(t) for t in a.text]
    hits = []
    for n in notes:
        d = local_date(n[a.date])
        if (a.since and d < a.since) or (a.until and d > a.until):
            continue
        hay = fold(n["name"]) if a.title_only else fold(n["name"] + "\n" + n.get("plaintext", ""))
        found = [t in hay for t in terms]
        if terms and not (any(found) if a.any else all(found)):
            continue
        hits.append({"title": n["name"], "folder": paths.get(n["folderId"], "?"),
                     "modified": n["modified"], "created": n["created"], "id": n["id"],
                     "locked": n["locked"],
                     "snippet": "" if n["locked"] else snippet(n.get("plaintext", ""), terms)})
    hits.sort(key=lambda h: h[a.date], reverse=True)
    total = len(hits)
    if a.limit:
        hits = hits[:a.limit]
    if a.json:
        L.dump({"count": total, "searched": len(notes), "results": hits})
        return
    print(f"{total} of {len(notes)} notes match" + (f" (showing {len(hits)})" if len(hits) < total else ""))
    for h in hits:
        lock = " [locked: title match only]" if h["locked"] else ""
        print(f"- {h['title']}  —  {h['folder']}  ({local_date(h['modified'])}){lock}")
        if h["snippet"] and terms:
            print(f"    {h['snippet']}")


if __name__ == "__main__":
    sys.exit(main())
