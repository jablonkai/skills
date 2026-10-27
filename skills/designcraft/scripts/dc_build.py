#!/usr/bin/env python3
"""Build a DesignCraft document from a JSON spec, headless, then save, render and export.

Spec (paths relative to the spec file; lengths are points or strings "3mm", "0.5in", "12pt"):

  {
    "document": "out/brochure.designcraft",
    "setup": {"preset": "A4", "pages": 4, "facingPages": true, "margins": "15mm",
              "bleed": "3mm", "columns": 1, "gutter": "5mm"},     # file.new params
    "styles": {
      "paragraph": [{"name": "Body", "chars": {"fontFamily": "Helvetica", "size": 10.5,
                     "leading": {"kind": "points", "value": 14}}, "para": {"spaceAfter": 6}}],
      "character": [{"name": "Strong", "chars": {"fontStyle": "Bold"}}]
    },
    "parent": [                                   # items on the A-Parent spread
      {"type": "text", "on": "both", "rect": ["15mm", "8mm", "-15mm", "14mm"],
       "text": "Northwind Trails", "style": "Header"},
      {"type": "text", "on": "both", "rect": ["15mm", "-12mm", "-15mm", "-6mm"],
       "text": "{page}", "style": "Folio"}                  # {page} = auto page number
    ],
    "items": [                                    # page numbers are 1-based
      {"type": "image", "page": 1, "rect": [0, 0, "-0", "-0"], "image": "photo1.jpg",
       "fit": "fillProportionally", "bleed": true},
      {"type": "text", "frames": [{"page": 2, "rect": "margins"}, {"page": 3, "rect": "margins"}],
       "textFile": "body.txt", "style": "Body",
       "rules": [{"regex": "^.{1,40}$", "style": "Heading"}]},
      {"type": "text", "page": 4, "rect": ["15mm", "200mm", "-15mm", "220mm"], "text": "…"},
      {"type": "rect", "page": 4, "rect": [0, 0, 100, 100], "fill": "C=100 M=0 Y=0 K=0"}
    ],
    "data": "people.csv",          # data-merge source; "{{name}}" in text = a field placeholder
    "png": [{"page": 1, "scale": 2, "out": "out/p1.png"}],          # page 1-based
    "pdf": {"out": "out/brochure.pdf", "standard": "x4", "bleed": true, "marks": true}
  }

Rects are [x0, y0, x1, y1] relative to the page's top-left; a negative value (or "-0")
counts from the right/bottom edge; "margins" is the page's margin box; "bleed": true
extends edges that touch the page out to the bleed. "on" (parent items): both | left |
right on facing pages. With "data", "{{column}}" in any text becomes a merge placeholder
(dc_merge.py then makes the records). `rules` restyle the story's paragraphs whose text matches a regex.
Text: "\n" starts a paragraph. Fails (and saves nothing) on any command error or on
overset text unless --allow-overset. File access is confined to the spec's folder, the
image/text folders (read) and the output folders (write). Refuses to overwrite without
--overwrite. Prints a JSON summary.
"""
import argparse
import json
import os
import re
import sys

from dclib import PAGE_MARKER, Session, ToolError, field_names, refuse_existing, validate_pdf

UNITS = {"pt": 1.0, "mm": 72 / 25.4, "cm": 72 / 2.54, "in": 72.0, "px": 1.0}
SETUP_LENGTHS = ("width", "height", "gutter", "margins", "bleed", "slug")


def length(v):
    """Points from a number or "3mm"; returns (value, negative) where "-0" counts as negative."""
    if isinstance(v, (int, float)):
        return float(v), v < 0
    m = re.fullmatch(r"\s*(-?)([\d.]+)\s*(pt|mm|cm|in|px)?\s*", str(v))
    if not m:
        raise ValueError("bad length %r" % v)
    val = float(m.group(2)) * UNITS[m.group(3) or "pt"]
    return (-val if m.group(1) else val), bool(m.group(1))


def pts(v):
    if isinstance(v, dict):
        return {k: pts(x) for k, x in v.items()}
    if isinstance(v, list):
        return [pts(x) for x in v]
    return length(v)[0]


def abspath(base, p):
    return os.path.abspath(os.path.join(base, os.path.expanduser(p)))


class Layout:
    """Page geometry after file.new: page number → spread index and x offset."""

    def __init__(self, insp, bleed):
        self.w = insp["settings"]["pageWidth"]
        self.h = insp["settings"]["pageHeight"]
        self.facing = insp["settings"]["facingPages"]
        self.bleed = bleed
        self.pages = {}
        for sp in insp["spreads"]:
            for pg in sp["pages"]:
                self.pages[pg["index"] + 1] = (sp["index"], pg["bounds"][0], pg["margins"], pg["side"])

    def rect(self, r, page_x, margins=None, side="right", bleed=False):
        if r == "margins":
            m = margins
            inside_left = side == "right" or not self.facing
            left = m["inside"] if inside_left else m["outside"]
            right = m["outside"] if inside_left else m["inside"]
            box = [left, m["top"], self.w - right, self.h - m["bottom"]]
        else:
            box = []
            for i, v in enumerate(r):
                val, neg = length(v)
                full = self.w if i % 2 == 0 else self.h
                box.append(full + val if neg else val)
        if bleed:
            b = self.bleed
            box[0] = box[0] - b if box[0] <= 0.01 else box[0]
            box[1] = box[1] - b if box[1] <= 0.01 else box[1]
            box[2] = box[2] + b if box[2] >= self.w - 0.01 else box[2]
            box[3] = box[3] + b if box[3] >= self.h - 0.01 else box[3]
        return [box[0] + page_x, box[1], box[2] + page_x, box[3]]


def story_text(item, base):
    if "textFile" in item:
        text = open(abspath(base, item["textFile"]), encoding="utf-8").read().rstrip("\n")
    else:
        text = item.get("text", "")
    return text.replace("{page}", PAGE_MARKER)


def style_steps(story, text, item):
    """Select whole story → paragraph style; then each rule's matching paragraphs."""
    steps = []
    raw = text.encode("utf-8")
    if item.get("style"):
        steps.append(("text.select", {"story": story, "anchor": 0, "focus": len(raw)}))
        steps.append(("style.paragraph.apply", {"name": item["style"]}))
    for rule in item.get("rules", []):
        pos = 0
        for para in text.split("\n"):
            n = len(para.encode("utf-8"))
            if re.search(rule["regex"], para):
                steps.append(("text.select", {"story": story, "anchor": pos, "focus": pos + n}))
                steps.append(("style.paragraph.apply", {"name": rule["style"]}))
            pos += n + 1
    return steps


FIELD = re.compile(r"\{\{(\w[\w ]*)\}\}")


def split_fields(text):
    """'Hi {{name}}' → ('Hi ', [(3, 'name')]): text without tokens, byte offsets of fields."""
    out, fields, pos = [], [], 0
    for m in FIELD.finditer(text):
        out.append(text[pos:m.start()])
        fields.append((len("".join(out).encode("utf-8")), m.group(1)))
        pos = m.end()
    out.append(text[pos:])
    return "".join(out), fields


def frame_steps(s, lay, item, base, spread, rect):
    """Create one item; return the result of its frame.create (id, story)."""
    kind = item.get("type", "text")
    if kind == "text":
        text, fields = split_fields(story_text(item, base))
        res = s.batch([("frame.create", {"spread": spread, "rect": rect, "content": "text",
                                         "text": text or " "})])[0]
        # placeholders first (last one first, so earlier offsets stay valid), then styles
        # over the story's final length: an empty paragraph would otherwise keep the default
        if fields:
            s.batch([("data.placeholder.add", {"field": f, "story": res["story"], "at": at})
                      for at, f in reversed(fields)])
            text = s.tool("get_story", {"story": res["story"]})["text"]
        follow = style_steps(res["story"], text, item)
        if follow:
            s.batch(follow)
        return res
    if kind == "image":
        res = s.batch([("frame.create", {"spread": spread, "rect": rect, "content": "graphic"})])[0]
        s.batch([("file.place", {"path": abspath(base, item["image"]), "frame": res["id"]}),
                 ("object.fit", {"mode": item.get("fit", "fillProportionally"), "ids": [res["id"]]})])
        return res
    if kind == "rect":
        res = s.batch([("frame.create", {"spread": spread, "rect": rect, "content": "unassigned"})])[0]
        if item.get("fill"):
            s.batch([("object.fill", {"swatch": item["fill"], "ids": [res["id"]]})])
        return res
    raise ValueError("unknown item type %r" % kind)


def build(spec, base, overwrite, allow_overset):
    doc = abspath(base, spec["document"])
    pdf = spec.get("pdf")
    pngs = spec.get("png", [])
    outputs = [doc] + ([abspath(base, pdf["out"])] if pdf else []) + [abspath(base, p["out"]) for p in pngs]
    refuse_existing(outputs, overwrite)
    for o in outputs:
        os.makedirs(os.path.dirname(o), exist_ok=True)

    reads = {base}
    if spec.get("data"):
        reads.add(os.path.dirname(abspath(base, spec["data"])))
    for it in spec.get("items", []) + spec.get("parent", []):
        for k in ("image", "textFile"):
            if k in it:
                reads.add(os.path.dirname(abspath(base, it[k])))
    s = Session(reads, {os.path.dirname(o) for o in outputs})
    try:
        setup = dict(spec.get("setup", {}))
        for k in SETUP_LENGTHS:
            if k in setup:
                setup[k] = pts(setup[k])
        s.tool("new_document", setup)
        insp = s.tool("inspect_document")
        bleed = pts(setup.get("bleed", 0))
        bleed = bleed[0] if isinstance(bleed, list) else bleed
        lay = Layout(insp, bleed)

        if spec.get("data"):
            src = s.cmd("data.source.select", {"path": abspath(base, spec["data"])})
            missing = sorted({f for it in spec.get("items", []) + spec.get("parent", [])
                              for f in FIELD.findall(it.get("text", ""))} - set(field_names(src)))
            if missing:
                raise ToolError("fields %s are not columns of %s (columns: %s)" % (
                    missing, spec["data"], field_names(src)))

        styles = spec.get("styles", {})
        steps = [("style.paragraph.create", st) for st in styles.get("paragraph", [])]
        steps += [("style.character.create", st) for st in styles.get("character", [])]
        if steps:
            s.batch(steps)

        parent = {"kind": "parent", "index": 0}
        for it in spec.get("parent", []):
            on = it.get("on", "both")
            sides = ["left", "right"] if lay.facing and on == "both" else [on if lay.facing else "right"]
            for side in sides:
                x = lay.w if lay.facing and side == "right" else 0.0
                margins = insp["spreads"][0]["pages"][0]["margins"]
                frame_steps(s, lay, it, base, parent, lay.rect(it["rect"], x, margins, side, it.get("bleed")))

        for it in spec.get("items", []):
            frames = it.get("frames") or [{"page": it["page"], "rect": it["rect"]}]
            prev = None
            for f in frames:
                spread, x, margins, side = lay.pages[f["page"]]
                rect = lay.rect(f["rect"], x, margins, side, it.get("bleed"))
                if prev is None:
                    prev = frame_steps(s, lay, it, base, spread, rect)
                else:
                    s.batch([("text.thread", {"from": prev["id"], "rect": rect, "spread": spread})])

        final = s.tool("inspect_document")
        overset = [st["id"] for st in final["stories"] if st.get("overset")]
        if overset and not allow_overset:
            raise ToolError("overset text in stories %s: add frames, enlarge them or reduce the "
                            "size (or pass --allow-overset); nothing saved" % overset)
        s.tool("save_document", {"path": doc})
        result = {"document": doc, "pages": final["pageCount"], "stories": len(final["stories"]),
                  "overset": overset}
        for p in pngs:
            out = abspath(base, p["out"])
            s.tool("export_png", {"page": p["page"] - 1, "path": out, "scale": p.get("scale", 1)})
            result.setdefault("png", []).append(out)
        if pdf:
            params = {k: v for k, v in pdf.items() if k != "out"}
            params["path"] = abspath(base, pdf["out"])
            result["pdf"] = s.cmd("file.exportPdf", params)
    finally:
        s.close()
    if pdf and pdf.get("standard") == "x4":
        v = validate_pdf(result["pdf"]["path"])
        result["validate"] = {"valid": v.get("valid"), "issues": v.get("issues")}
        if not v.get("valid"):
            print(json.dumps(result, indent=2))
            sys.exit("PDF/X-4 validation failed")
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--allow-overset", action="store_true")
    a = ap.parse_args()
    spec_path = os.path.abspath(a.spec)
    spec = json.load(open(spec_path))
    try:
        res = build(spec, os.path.dirname(spec_path), a.overwrite, a.allow_overset)
    except (ToolError, ValueError, KeyError) as e:
        sys.exit("dc_build: %s" % e)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
