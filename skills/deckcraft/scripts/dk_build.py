#!/usr/bin/env python3
"""Build a DeckCraft presentation from a Markdown outline, headless, then read it back.

  dk_build.py OUTLINE.md --out deck.deckcraft [--theme Harbor] [--pptx deck.pptx]
              [--pdf deck.pdf] [--notes-pdf notes.pdf] [--png-dir DIR] [--size standard]
              [--overwrite] [--dry-run]

Outline rules (one slide per heading, in order):
  # Title            the first H1 is the title slide; the first plain line under it is
                     the subtitle. A later H1 is a section header slide.
  ## Slide title     a content slide. `-`, `*` or `1.` items are bullets; indent by two
                     spaces (or a tab) per level. Plain lines are body paragraphs.
  ![alt](photo.jpg)  a picture on the slide (path relative to the outline), fitted under
                     the title; with bullets too, the slide becomes Two Content with the
                     picture in the right-hand box.
  Notes: text        presenter notes for the slide (`> text` lines work too; several
                     lines are joined as paragraphs).
  ---, blank lines   ignored.

The starter slide that every new presentation has is removed, so the deck holds exactly
the outline's slides. An unknown --theme fails (DeckCraft would silently use the default).
Outputs are never overwritten without --overwrite. After saving, the file is read back
with `deckcraft-cli info` and the slide count, titles, layouts, notes and pictures are
compared with the outline; any mismatch exits 1. Prints a JSON summary.
"""
import argparse
import json
import os
import re
import sys

from dklib import (Session, ToolError, fit, image_size, info, inspect, refuse_existing,
                   run_cli, SLIDE_H)

BULLET = re.compile(r"^(\s*)(?:[-*+]|\d+[.)])\s+(.*)$")
IMAGE = re.compile(r"^!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)\s*$")
NOTES = re.compile(r"^(?:notes?|speaker notes)\s*:\s*(.*)$", re.I)


def parse(text, base):
    slides = []
    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        m = re.match(r"^(#{1,2})\s+(.*)$", stripped)
        if m:
            kind = "title" if m.group(1) == "#" and not slides else (
                "section" if m.group(1) == "#" else "content")
            slides.append({"kind": kind, "title": m.group(2).strip(), "body": [], "images": [],
                           "notes": []})
            continue
        if not stripped or stripped in ("---", "***") or not slides:
            continue
        s = slides[-1]
        n = NOTES.match(stripped)
        if n or stripped.startswith(">"):
            s["notes"].append(n.group(1) if n else stripped.lstrip(">").strip())
            continue
        im = IMAGE.match(stripped)
        if im:
            path = os.path.normpath(os.path.join(base, im.group(2)))
            s["images"].append({"alt": im.group(1), "path": path})
            continue
        b = BULLET.match(line.expandtabs(2))
        if b:
            s["body"].append("\t" * (len(b.group(1)) // 2) + b.group(2).strip())
        else:
            s["body"].append(stripped)
    return slides


def layout_of(s):
    if s["kind"] == "title":
        return "title"
    if s["kind"] == "section":
        return "sectionHeader"
    if s["images"]:
        return "twoContent" if s["body"] else "titleOnly"
    return "titleAndContent" if s["body"] else "titleOnly"


LAYOUT_NAMES = {"title": "Title Slide", "sectionHeader": "Section Header", "twoContent": "Two Content",
                "titleOnly": "Title Only", "titleAndContent": "Title and Content"}


def picture_box(sess, index, layout):
    """Where a picture goes: the empty right-hand content box, or the area under the title."""
    shapes = sess.slide(index)["shapes"]
    if layout == "twoContent":
        empty = [s for s in shapes if s.get("kind") == "placeholder" and not s.get("text")
                 and s.get("placeholder") not in ("title", "ctrTitle", "dt", "ftr", "sldNum")]
        if empty:
            return max(empty, key=lambda s: s["box"][0])["box"]
    title = next((s["box"] for s in shapes if s.get("placeholder") in ("title", "ctrTitle")), None)
    x, y, w, h = title or [60, 36, 840, 90]
    top = y + h + 12
    return [x, top, w, SLIDE_H - top - 36]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("outline")
    ap.add_argument("--out", help=".deckcraft (or .pptx) to write; required unless --dry-run")
    ap.add_argument("--theme", help="DeckCraft, Harbor, Ember, Meadow, Nocturne, Paper, Coral Reef, Slate")
    ap.add_argument("--pptx")
    ap.add_argument("--pdf")
    ap.add_argument("--notes-pdf", help="PDF of notes pages (slide image + notes)")
    ap.add_argument("--png-dir", help="render every slide to DIR/slide-01.png …")
    ap.add_argument("--size", choices=["widescreen", "standard"], help="16:9 (default) or 4:3")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="print the parsed slides and stop")
    a = ap.parse_args()

    outline = os.path.realpath(a.outline)
    slides = parse(open(outline, encoding="utf-8").read(), os.path.dirname(outline))
    if not slides:
        sys.exit("no slides: the outline needs at least one # or ## heading")
    for s in slides:
        s["layout"] = layout_of(s)
    if a.dry_run:
        print(json.dumps(slides, indent=1, ensure_ascii=False))
        return
    if not a.out:
        ap.error("--out is required")
    missing = [i["path"] for s in slides for i in s["images"] if not os.path.isfile(i["path"])]
    if missing:
        sys.exit("missing images: " + ", ".join(missing))
    outs = [p for p in (a.out, a.pptx, a.pdf, a.notes_pdf) if p]
    png_busy = a.png_dir and os.path.isdir(a.png_dir) and os.listdir(a.png_dir)
    refuse_existing(outs + ([a.png_dir] if png_busy else []), a.overwrite)
    for p in outs:
        os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)

    reads = {os.path.dirname(outline)} | {os.path.dirname(i["path"]) for s in slides for i in s["images"]}
    writes = {os.path.dirname(os.path.abspath(p)) for p in outs}
    sess = Session(reads, writes)
    try:
        sess.tool("new_presentation", {})
        if a.theme:
            themes = sess.themes()
            if a.theme not in themes:
                sys.exit("unknown theme %r; DeckCraft has: %s" % (a.theme, ", ".join(themes)))
            sess.cmd("design.theme", {"name": a.theme})
        if a.size:
            sess.cmd("design.slideSize", {"preset": a.size})
        sess.cmd("slide.delete", {"index": 0})
        for i, s in enumerate(slides):
            params = {"layout": s["layout"], "title": s["title"], "at": i}
            if s["body"]:
                params["body"] = "\n".join(s["body"])
            sess.cmd("slide.new", params)
            if s["notes"]:
                sess.cmd("slide.notes", {"index": i, "text": "\n".join(s["notes"])})
            if s["images"]:
                sess.cmd("slide.go", {"index": i})
                box = picture_box(sess, i, s["layout"])
                n = len(s["images"])
                for k, im in enumerate(s["images"]):  # several pictures share the box side by side
                    cell = [box[0] + k * box[2] / n, box[1], box[2] / n, box[3]]
                    sess.cmd("insert.picture", {"path": im["path"], "rect": fit(image_size(im["path"]), cell)})
        sess.save_as(a.out)
        if a.pptx:
            sess.save_as(a.pptx)
        if a.pdf:
            sess.export(a.pdf)
        if a.notes_pdf:
            sess.export(a.notes_pdf, layout="notes")
    except ToolError as e:
        sys.exit("DeckCraft refused a command, nothing verified: %s" % e)
    finally:
        sess.close()
    if a.png_dir:
        run_cli(["render", a.out, "--all", a.png_dir])

    problems, report = [], {"out": a.out, "slides": []}
    for path in [a.out] + ([a.pptx] if a.pptx else []):
        d = info(path)
        if len(d["slides"]) != len(slides):
            problems.append("%s: %d slides, outline has %d" % (path, len(d["slides"]), len(slides)))
        for s, got in zip(slides, d["slides"]):
            want_notes = "\n".join(s["notes"])
            if got["title"] != s["title"]:
                problems.append("%s slide %d: title %r, want %r" % (path, got["index"] + 1, got["title"], s["title"]))
            if got["notes"].strip() != want_notes:
                problems.append("%s slide %d: notes %r, want %r" % (path, got["index"] + 1, got["notes"], want_notes))
            if got["layout"] != LAYOUT_NAMES[s["layout"]]:
                problems.append("%s slide %d: layout %r" % (path, got["index"] + 1, got["layout"]))
            if path == a.out:
                pics = 0
                if s["images"]:
                    pics = sum(1 for sh in inspect(path, got["index"])["shapes"] if sh.get("kind") == "picture")
                    if pics != len(s["images"]):
                        problems.append("slide %d: %d pictures, want %d" % (got["index"] + 1, pics, len(s["images"])))
                report["slides"].append({"slide": got["index"] + 1, "title": got["title"], "layout": got["layout"],
                                         "bullets": len(s["body"]), "pictures": pics, "notes": bool(got["notes"])})
        if path == a.out:
            report["theme"] = d.get("theme")
            if a.theme and d.get("theme") != a.theme:
                problems.append("theme %r, want %r" % (d.get("theme"), a.theme))
    report["outputs"] = [p for p in outs if os.path.exists(p)] + ([a.png_dir] if a.png_dir else [])
    report["problems"] = problems
    print(json.dumps(report, indent=1, ensure_ascii=False))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
