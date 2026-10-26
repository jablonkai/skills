#!/usr/bin/env python3
"""Read WordCraft documents back and check the result.

    wc_verify.py doc FILE.docx [--blocks N]     structure: blocks with styles, tables, parts,
                                                placeholders left, revisions and comments
                                                WITH AUTHORS (from the XML), TOC entries
    wc_verify.py doc FILE.docx --no-placeholders --author NAME --style 'Heading 1=Intro' …
                                                the same, exit 1 if a check fails
    wc_verify.py files DIR --ext docx [--count N]   outputs present, PDF page counts
    wc_verify.py hash DIR > before.sha256 ; wc_verify.py hash DIR --check before.sha256

`wordcraft-cli inspect` has no author names; this is where they are read.
"""
import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wclib import inspect, pdf_pages, placeholders, review_marks  # noqa: E402


def norm_style(s):
    return str(s or "").replace(" ", "").lower()


def cmd_doc(a):
    d = inspect(a.file)
    blocks = []
    for b in d["blocks"][:a.blocks]:
        e = {"i": b.get("index"), "type": b.get("type"), "style": b.get("style")}
        if b.get("type") == "table":
            e["cells"] = b.get("cells")
        else:
            e["text"] = b.get("text", "")[:120]
            fields = [o.get("instr") for o in b.get("objects", []) if o.get("type") == "field"]
            if fields:
                e["fields"] = fields
            if any("ins" in r.get("props", {}) or "del" in r.get("props", {}) for r in b.get("runs", [])):
                e["revised"] = True
        blocks.append(e)
    marks = review_marks(a.file) if a.file.lower().endswith(".docx") else {}
    left = placeholders(d)
    report = {"pages": d.get("pages"), "words": d.get("words"), "trackChanges": d.get("trackChanges"),
              "blocks": blocks, "more_blocks": max(0, len(d["blocks"]) - a.blocks),
              "parts": [{"id": p["id"], "kind": p["kind"], "text": p.get("text", "")[:120]}
                        for p in d.get("parts", [])],
              "placeholders_left": left, **marks}
    fails = []
    if a.no_placeholders and left:
        fails.append("placeholders left: %s" % sorted(left))
    if a.author:
        wrong = [m for m in marks.get("revisions", []) + marks.get("comments", []) if m.get("author") != a.author]
        if wrong or not (marks.get("revisions") or marks.get("comments")):
            fails.append("marks not all by %r: %s" % (a.author, wrong or "no marks"))
    for spec in a.style or []:
        style, _, text = spec.partition("=")
        hit = [b for b in d["blocks"] if b.get("text", "").strip() == text.strip()]
        if not hit or norm_style(hit[0].get("style")) != norm_style(style):
            fails.append("%r is %s, not %s" % (text, hit and hit[0].get("style"), style))
    report["failures"] = fails
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 1 if fails else 0


def cmd_files(a):
    files = sorted(f for f in os.listdir(a.dir) if not a.ext or f.lower().endswith("." + a.ext.lower()))
    out = []
    for f in files:
        p = os.path.join(a.dir, f)
        e = {"file": f, "bytes": os.path.getsize(p)}
        if f.lower().endswith(".pdf"):
            e["pages"] = pdf_pages(p)
        out.append(e)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 1 if a.count is not None and len(files) != a.count else 0


def cmd_hash(a):
    lines = []
    for root, _, names in os.walk(a.dir):
        for n in sorted(names):
            p = os.path.join(root, n)
            lines.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), os.path.relpath(p, a.dir)))
    lines.sort(key=lambda s: s.split("  ", 1)[1])
    if a.check:
        want = open(a.check).read().split("\n")
        changed = sorted(set(filter(None, want)) ^ set(lines))
        print(json.dumps({"unchanged": not changed, "differences": changed}, indent=1))
        return 1 if changed else 0
    print("\n".join(lines))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("doc")
    p.add_argument("file")
    p.add_argument("--blocks", type=int, default=60)
    p.add_argument("--no-placeholders", action="store_true")
    p.add_argument("--author")
    p.add_argument("--style", action="append", help="'Style name=paragraph text' (repeatable)")
    p = sub.add_parser("files")
    p.add_argument("dir")
    p.add_argument("--ext")
    p.add_argument("--count", type=int)
    p = sub.add_parser("hash")
    p.add_argument("dir")
    p.add_argument("--check")
    a = ap.parse_args()
    return {"doc": cmd_doc, "files": cmd_files, "hash": cmd_hash}[a.mode](a)


if __name__ == "__main__":
    sys.exit(main())
