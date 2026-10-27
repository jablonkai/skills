#!/usr/bin/env python3
"""Check PDFs against expectations by reading them back with pdfcraft-cli.
Prints JSON and exits 1 when any check fails.

  pf_verify.py PATH... [checks]

PATH is a PDF or a folder (its *.pdf files). Checks apply to every file:

  --pages N                    page count
  --rotation SPEC              per-page rotation, e.g. "8=90" or "1-7=0,8=90";
                               "*=0" for all pages, "last=90" for the final page
  --title T / --author A       document info entries (exact match)
  --contains S                 text somewhere in the document (case-insensitive)
  --absent S                   text nowhere in the document, nor in the title,
                               subject, keywords or bookmarks (case-insensitive)
  --page-order S1,S2,…         page i contains S_i, and the page count equals the list
  --searchable                 every page has extractable text
  --audit-clean                `audit` finds no faux redactions or unapplied marks
  --valid                      `check` opens and renders the file
  --count N                    number of PDFs found across the PATHs
"""

import argparse
import glob
import json
import os
import sys

import pflib


def expand(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            files += sorted(glob.glob(os.path.join(p, "*.pdf")))
        else:
            files.append(p)
    return files


def parse_rotation(spec, count):
    want = {}
    for part in spec.split(","):
        pages, _, deg = part.partition("=")
        deg = int(deg)
        pages = pages.strip()
        if pages == "*":
            nums = range(1, count + 1)
        elif pages == "last":
            nums = [count]
        elif "-" in pages:
            lo, hi = pages.split("-")
            nums = range(int(lo), int(hi) + 1)
        else:
            nums = [int(pages)]
        for n in nums:
            want[n] = deg % 360
    return want


def outline_titles(items):
    for b in items or []:
        yield b.get("title", "")
        yield from outline_titles(b.get("children"))


def verify(path, a):
    checks = []

    def add(name, ok, detail):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    if not os.path.exists(path):
        add("exists", False, "missing")
        return checks
    info = pflib.doc_info(path)
    pages = info.get("pages") or []
    count = len(pages)
    texts = None

    def text():
        nonlocal texts
        if texts is None:
            texts = pflib.page_texts(path, count)
        return texts

    if a.pages is not None:
        add("pages", count == a.pages, f"{count} (want {a.pages})")
    if a.rotation:
        want = parse_rotation(a.rotation, count)
        got = {i: (p.get("rotation") or 0) % 360 for i, p in enumerate(pages, 1)}
        wrong = {n: got.get(n) for n, d in want.items() if got.get(n) != d}
        add("rotation", not wrong, "ok" if not wrong else f"actual by page {wrong} (want {a.rotation})")
    if a.title is not None:
        add("title", info.get("title") == a.title, repr(info.get("title")))
    if a.author is not None:
        add("author", info.get("author") == a.author, repr(info.get("author")))
    for s in a.contains:
        hits = [i for i, t in enumerate(text(), 1) if s.lower() in t.lower()]
        add(f"contains {s!r}", hits, f"pages {hits}" if hits else "not found")
    for s in a.absent:
        hits = [i for i, t in enumerate(text(), 1) if s.lower() in t.lower()]
        meta = [k for k in ("title", "subject", "keywords")
                if s.lower() in str(info.get(k) or "").lower()]
        if any(s.lower() in t.lower() for t in outline_titles(info.get("outline"))):
            meta.append("bookmarks")
        add(f"absent {s!r}", not hits and not meta,
            "absent" if not hits and not meta else f"pages {hits} {meta}".strip())
    if a.page_order:
        want = [w.strip() for w in a.page_order.split(",")]
        bad = [i for i, w in enumerate(want, 1)
               if i > count or w.lower() not in text()[i - 1].lower()]
        add("page-order", not bad and count == len(want),
            "ok" if not bad and count == len(want) else f"{count} pages; mismatched positions {bad}")
    if a.searchable:
        empty = [i for i, t in enumerate(text(), 1) if not t.strip()]
        add("searchable", not empty, "every page has text" if not empty else f"no text on pages {empty}")
    if a.audit_clean:
        data, rc = pflib.audit(path)
        add("audit-clean", rc == 0 and data.get("count", 1) == 0,
            f"{data.get('count')} finding(s)" + (
                f": {[f.get('kind') + ' p' + str(f.get('page')) for f in data.get('findings', [])]}"
                if data.get("count") else ""))
    if a.valid:
        p = pflib.run_cli(["check", path])
        add("valid", p.returncode == 0, (p.stdout or p.stderr).strip()[-200:])
    return checks


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--pages", type=int)
    ap.add_argument("--rotation")
    ap.add_argument("--title")
    ap.add_argument("--author")
    ap.add_argument("--contains", action="append", default=[])
    ap.add_argument("--absent", action="append", default=[])
    ap.add_argument("--page-order")
    ap.add_argument("--searchable", action="store_true")
    ap.add_argument("--audit-clean", action="store_true")
    ap.add_argument("--valid", action="store_true")
    ap.add_argument("--count", type=int)
    a = ap.parse_args()

    files = expand(a.paths)
    out = {"files": {}, "ok": True}
    if a.count is not None:
        ok = len(files) == a.count
        out["count"] = {"ok": ok, "detail": f"{len(files)} (want {a.count})"}
        out["ok"] &= ok
    for f in files:
        checks = verify(f, a)
        out["files"][f] = checks
        out["ok"] &= all(c["ok"] for c in checks)
    print(json.dumps(out, indent=2))
    sys.exit(0 if out["ok"] else 1)


if __name__ == "__main__":
    main()
