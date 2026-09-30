#!/usr/bin/env python3
"""Build a Keynote deck from a Markdown or JSON outline.

  keynote-build.py OUTLINE.md|OUTLINE.json --out DECK.key [--theme ID|NAME]
                   [--export FILE.pdf|.pptx|.png|...]... [export options] [--force]
                   [--dry-run]

Markdown outline, one slide per heading:
  # Deck title        first H1: title slide; plain lines below it are the subtitle
  # Section name      any later H1: section slide
  ## Slide title      content slide (### and deeper too)
  - bullet            bullets (-, *, +, 1.); nested bullets are flattened (Keynote
                      has no scriptable indent level) and reported as a warning
  plain line          body text, one paragraph per line
  ![alt](pic.png)     image, relative to the outline; fills the layout's photo
                      placeholder, else sits in the right half
  Notes: text         presenter notes: this line and every line after it until the
                      next heading
  <!-- layout: X -->  layout override: role, English or localized name, or index
  <!-- skip -->       mark the slide skipped
  ---                 ignored (slide separators from other tools)

JSON outline: {"theme": "...", "slides": [{"title", "body": str|[str], "notes",
  "image", "layout", "skip", "section": bool}]}

Roles picked automatically: title, section, bullets, bullets-photo, title-photo,
photo, title-only. Other roles: statement, quote, agenda, blank. Layout names are
resolved through the running Keynote, so this works in any UI language.

Prints JSON lines (slides, warnings, exports) and a summary. Exit 0 on success.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import keynote_osa as ko  # noqa: E402

BULLET = re.compile(r"^(\s*)(?:[-*+]|\d+[.)])\s+(.*)$")
IMAGE = re.compile(r"^!\[[^\]]*\]\(\s*<?([^)>]+?)>?\s*\)\s*$")
DIRECTIVE = re.compile(r"^<!--\s*(layout|skip)\s*:?\s*(.*?)\s*-->$", re.I)
NOTES = re.compile(r"^(?:notes|speaker notes)\s*:\s*(.*)$", re.I)


def parse_markdown(text, base):
    slides, warnings, cur, h1_seen = [], [], None, False
    in_notes = False
    for raw in text.splitlines():
        line = raw.rstrip()
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if m:
            level, title = len(m.group(1)), m.group(2)
            role = None
            if level == 1:
                role = "section" if h1_seen else "title"
                h1_seen = True
            cur = {"title": title, "body": [], "notes": [], "image": None,
                   "layout": None, "skip": False, "role": role}
            slides.append(cur)
            in_notes = False
            continue
        if cur is None:
            if line.strip():
                warnings.append("text before the first heading ignored: %r" % line.strip()[:40])
            continue
        if in_notes:
            cur["notes"].append(line.strip())
            continue
        stripped = line.strip()
        if not stripped or stripped == "---":
            continue
        d = DIRECTIVE.match(stripped)
        if d:
            if d.group(1).lower() == "skip":
                cur["skip"] = True
            else:
                cur["layout"] = d.group(2)
            continue
        n = NOTES.match(stripped)
        if n:
            in_notes = True
            if n.group(1):
                cur["notes"].append(n.group(1))
            continue
        im = IMAGE.match(stripped)
        if im:
            if cur["image"]:
                warnings.append("slide %r: only the first image is placed" % cur["title"])
            else:
                cur["image"] = os.path.join(base, im.group(1))
            continue
        b = BULLET.match(line)
        if b:
            if len(b.group(1).expandtabs(4)) >= 2:
                warnings.append("slide %r: nested bullet flattened: %r" % (cur["title"], b.group(2)[:40]))
            cur["body"].append(b.group(2))
            continue
        cur["body"].append(stripped)
    for s in slides:
        s["notes"] = "\n".join(s["notes"]).strip()
    return None, slides, warnings


def parse_json(text, base):
    data = json.loads(text)
    slides = []
    for i, s in enumerate(data.get("slides", [])):
        body = s.get("body") or []
        if isinstance(body, str):
            body = body.split("\n")
        role = None
        if s.get("section"):
            role = "section"
        elif i == 0 and not s.get("image") and len(body) <= 2:
            role = "title"
        img = s.get("image")
        slides.append({"title": s.get("title") or "", "body": body, "notes": s.get("notes") or "",
                       "image": os.path.join(base, img) if img else None,
                       "layout": s.get("layout"), "skip": bool(s.get("skip")), "role": role})
    return data.get("theme"), slides, []


def pick_role(s):
    if s["role"]:
        return s["role"]
    if s["image"]:
        if s["body"]:
            return "bullets-photo"
        return "title-photo" if s["title"] else "photo"
    return "bullets" if s["body"] else "title-only"


def main(argv):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("outline")
    ap.add_argument("--out", required=True, help="deck to write (.key)")
    ap.add_argument("--theme", help="theme id or name (default: Basic White)")
    ap.add_argument("--export", action="append", default=[],
                    help="also export to FILE; format from the extension")
    ap.add_argument("--force", action="store_true", help="replace existing outputs")
    ap.add_argument("--dry-run", action="store_true", help="print the plan, touch nothing")
    ko.add_export_args(ap)
    ns = ap.parse_args(argv)

    try:
        if not ns.out.endswith(".key"):
            raise ko.KeynoteError("--out must end in .key")
        with open(ns.outline, encoding="utf-8-sig") as fh:
            text = fh.read()
        base = os.path.dirname(os.path.abspath(ns.outline))
        is_json = ns.outline.lower().endswith(".json")
        theme, slides, warnings = (parse_json if is_json else parse_markdown)(text, base)
        if not slides:
            raise ko.KeynoteError("the outline has no slides (no headings / empty slides list)")
        theme_id = ko.resolve_theme(ns.theme or theme)
        layouts = ko.theme_layouts(theme_id)

        out = ko.real(ns.out)
        exports = [(ko.real(p), ko.format_of(p)) for p in ns.export]
        for path in [out] + [p for p, _ in exports]:
            if os.path.exists(path):
                if not ns.force:
                    raise ko.KeynoteError("exists (use --force): %s" % path)
                if not ns.dry_run:
                    ko.remove_path(path)

        args = [out, theme_id]
        plan = []
        for i, s in enumerate(slides, 1):
            lay = ko.resolve_layout(layouts, s["layout"] or pick_role(s))
            args += ["SL", lay["index"]]
            if s["title"]:
                args += ["TI", s["title"]]
            if s["body"]:
                args += ["BO", "\n".join(s["body"])]
            if s["notes"]:
                args += ["NO", s["notes"]]
            if s["image"]:
                if not os.path.isfile(s["image"]):
                    raise ko.KeynoteError("slide %d: image not found: %s" % (i, s["image"]))
                args += ["IM", os.path.realpath(s["image"])]
            if s["skip"]:
                args += ["SK"]
            if s["title"] and not lay["title"]:
                warnings.append("slide %d: layout %r has no title placeholder; it is shown anyway"
                                % (i, lay["name"]))
            plan.append({"slide": i, "layout": lay["name"], "title": s["title"],
                         "bullets": len(s["body"]), "notes": bool(s["notes"]),
                         "image": bool(s["image"]), "skip": s["skip"]})
        args += ko.export_opt_args(ns)
        for path, fmt in exports:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            args += ["X", path, fmt]

        for p in plan:
            print(json.dumps(p, ensure_ascii=False))
        for w in warnings:
            print(json.dumps({"warning": w}, ensure_ascii=False))
        if ns.dry_run:
            print(json.dumps({"ok": True, "dry_run": True, "theme": theme_id, "slides": len(plan)}))
            return 0

        os.makedirs(os.path.dirname(out), exist_ok=True)
        res = ko.rows(ko.run_ops("build", args, docs=[out]))
    except (ko.KeynoteError, OSError, ValueError) as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        return 1

    count = next((int(r[1]) for r in res if r[0] == "SLIDES"), None)
    done = [r[1] for r in res if r[0] == "EXPORTED"]
    missing = [p for p, _ in exports if not os.path.exists(p)]
    ok = count == len(plan) and not missing
    print(json.dumps({"ok": ok, "out": out, "theme": theme_id, "slides": count,
                      "expected_slides": len(plan), "exported": done, "missing": missing},
                     ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
