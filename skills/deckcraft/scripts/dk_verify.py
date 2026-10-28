#!/usr/bin/env python3
"""Read back DeckCraft output and check it. Prints JSON; exits 1 if any check fails.

  dk_verify.py deck F [--slides 6] [--titles T1 T2 …] [--layout 1="Title Slide"]
                      [--notes 2="Open with…"] [--only-notes 2 4 6] [--text 3="Fuel per"]
                      [--pictures 5=1] [--theme Harbor] [--no-empty]
  dk_verify.py pdf F.pdf [--pages 5] [--size 960x540] [--order T1 T2 …] [--text 2="…"]
  dk_verify.py png F.png [--size 1920x1080 | --width 480] [--not-blank]
  dk_verify.py hash PATH… [--save manifest.json | --compare manifest.json]

Slide and page numbers are 1-based. With no checks, `deck` prints a summary: every
slide's title, layout, notes, picture count and text.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

from dklib import image_size, info, inspect, sha256, slide_text

checks = []


def check(name, ok, got):
    checks.append({"check": name, "ok": bool(ok), "got": got})


def pairs(items):
    out = {}
    for item in items or []:
        k, _, v = item.partition("=")
        out[int(k)] = v
    return out


def deck(a):
    d = info(a.file)
    slides = d["slides"]
    detail = {}

    def slide(n):
        if n not in detail:
            detail[n] = inspect(a.file, n - 1)
        return detail[n]

    summary = []
    for s in slides:
        n = s["index"] + 1
        pics = sum(1 for sh in slide(n)["shapes"] if sh.get("kind") == "picture")
        summary.append({"slide": n, "title": s["title"], "layout": s["layout"], "hidden": s["hidden"],
                        "notes": s["notes"], "pictures": pics, "text": slide_text(slide(n))})
    if a.slides is not None:
        check("slides == %d" % a.slides, len(slides) == a.slides, len(slides))
    if a.titles:
        got = [s["title"] for s in slides]
        check("titles in order", got == a.titles, got)
    for n, want in pairs(a.layout).items():
        got = slides[n - 1]["layout"] if n <= len(slides) else None
        check("slide %d layout %s" % (n, want), got == want, got)
    for n, want in pairs(a.notes).items():
        got = slides[n - 1]["notes"].strip() if n <= len(slides) else None
        check("slide %d notes" % n, got == want, got)
    if a.only_notes is not None:
        got = [s["index"] + 1 for s in slides if s["notes"].strip()]
        check("notes only on %s" % a.only_notes, got == sorted(a.only_notes), got)
    for n, want in pairs(a.text).items():
        got = slide_text(slide(n)) if n <= len(slides) else ""
        check("slide %d contains %r" % (n, want), want in got, got)
    for n, want in pairs(a.pictures).items():
        got = summary[n - 1]["pictures"] if n <= len(slides) else None
        check("slide %d pictures == %s" % (n, want), got == int(want), got)
    if a.theme:
        check("theme %s" % a.theme, d.get("theme") == a.theme, d.get("theme"))
    if a.no_empty:
        empty = [s["slide"] for s in summary if not s["title"] and not s["text"].strip() and not s["pictures"]]
        check("no empty slides", not empty, empty)
    return {"file": a.file, "theme": d.get("theme"), "slideSize": d.get("slideSize"),
            "media": len(d.get("media", [])), "slides": summary}


def pdf(a):
    if not shutil.which("pdfinfo"):
        sys.exit("pdfinfo/pdftotext not found: brew install poppler")
    meta = subprocess.run(["pdfinfo", a.file], capture_output=True, text=True).stdout
    pages = next((int(l.split()[1]) for l in meta.splitlines() if l.startswith("Pages:")), 0)
    size = next((l.split(":", 1)[1].strip() for l in meta.splitlines() if l.startswith("Page size:")), "")

    def text(n):
        return subprocess.run(["pdftotext", "-f", str(n), "-l", str(n), a.file, "-"],
                              capture_output=True, text=True).stdout

    if a.pages is not None:
        check("pages == %d" % a.pages, pages == a.pages, pages)
    if a.size:
        w, h = a.size.lower().split("x")
        check("page size %s pt" % a.size, size.startswith("%s x %s" % (w, h)), size)
    if a.order:
        firsts = [text(n) for n in range(1, pages + 1)]
        bad = [t for i, t in enumerate(a.order) if i >= pages or t not in firsts[i]]
        check("page order", len(a.order) == pages and not bad,
              [f.strip().split("\n")[0] if f.strip() else "" for f in firsts])
    for n, want in pairs(a.text).items():
        got = text(n)
        check("page %d contains %r" % (n, want), want in got, got.strip()[:200])
    return {"file": a.file, "pages": pages, "size": size}


def png(a):
    size = image_size(a.file)
    if a.size:
        want = tuple(int(v) for v in a.size.lower().split("x"))
        check("size %s" % a.size, size == want, size)
    if a.width:
        check("width %d" % a.width, size and abs(size[0] - a.width) <= 2, size)
    if a.not_blank:
        if not shutil.which("magick"):
            sys.exit("--not-blank needs ImageMagick (magick)")
        sd = float(subprocess.run(["magick", "identify", "-format", "%[fx:standard_deviation]", a.file],
                                  capture_output=True, text=True).stdout or 0)
        check("not blank", sd > 0.01, round(sd, 4))
    return {"file": a.file, "size": size}


def hashes(a):
    now = {p: sha256(p) for p in a.paths}
    if a.save:
        json.dump(now, open(a.save, "w"), indent=1)
    if a.compare:
        old = json.load(open(a.compare))
        changed = [p for p in old if now.get(p, sha256(p) if os.path.exists(p) else None) != old[p]]
        check("unchanged since %s" % a.compare, not changed, changed)
    return {"hashes": now}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)
    d = sub.add_parser("deck")
    d.add_argument("file")
    d.add_argument("--slides", type=int)
    d.add_argument("--titles", nargs="+")
    d.add_argument("--layout", action="append", metavar="N=NAME")
    d.add_argument("--notes", action="append", metavar="N=TEXT")
    d.add_argument("--only-notes", type=int, nargs="*", metavar="N")
    d.add_argument("--text", action="append", metavar="N=TEXT")
    d.add_argument("--pictures", action="append", metavar="N=COUNT")
    d.add_argument("--theme")
    d.add_argument("--no-empty", action="store_true")
    p = sub.add_parser("pdf")
    p.add_argument("file")
    p.add_argument("--pages", type=int)
    p.add_argument("--size", help="WxH in points, e.g. 960x540")
    p.add_argument("--order", nargs="+", help="text expected on page 1, 2, …")
    p.add_argument("--text", action="append", metavar="N=TEXT")
    i = sub.add_parser("png")
    i.add_argument("file")
    i.add_argument("--size")
    i.add_argument("--width", type=int)
    i.add_argument("--not-blank", action="store_true")
    h = sub.add_parser("hash")
    h.add_argument("paths", nargs="+")
    h.add_argument("--save")
    h.add_argument("--compare")
    a = ap.parse_args()

    result = {"deck": deck, "pdf": pdf, "png": png, "hash": hashes}[a.mode](a)
    result["checks"] = checks
    result["ok"] = all(c["ok"] for c in checks)
    print(json.dumps(result, indent=1, ensure_ascii=False))
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
