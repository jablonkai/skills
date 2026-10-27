#!/usr/bin/env python3
"""Read FigCraft results back and check them. Prints JSON; exits 1 when any check fails.

    fc_verify.py doc FILE [checks]        a .figcraft/.fig/.json document, via inspect
        --frames N                        number of top-level layers (all pages)
        --frame Login=390x844             a top-level layer of that size
        --text Title="Welcome back"       a layer's characters (name, or Frame/Name)
        --has-text "Sign in"              some text layer contains this
        --names Email Password            layers with these names exist
        --component Button                a main component of that name exists
        --instance Button@Login           an instance of it (optionally under that frame);
                                          a set name or a variant name like Style=Secondary
        --auto-layout Login               the layer uses auto layout
        --style H1                        a style of that name exists
        --text-style "Welcome back=H1"    text with these characters uses that text style
        --fill Login/Email                the layer stretches with its auto-layout parent
        --no-notes                        nothing was dropped on import (info notes)
        --fonts-ok                        no missing fonts
    fc_verify.py files DIR|FILE… [checks]
        --ext png  --count 3  --px 780x1688 [WxH…]  --svg  --pdf-pages 1
        --trim 255x156 (pt)  --bleed 3mm  --marks (MediaBox larger than the BleedBox)
    fc_verify.py hash DIR [--compare manifest.json]   sha256 of every file in DIR
"""
import argparse
import glob
import hashlib
import json
import os
import re
import struct
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fclib import Session, info  # noqa: E402

UNITS = {"pt": 1.0, "mm": 72 / 25.4, "in": 72.0, "px": 1.0}


def length_pt(text):
    m = re.fullmatch(r"([\d.]+)\s*(pt|mm|in|px)?", text.strip())
    if not m:
        raise SystemExit("bad length: %s" % text)
    return float(m.group(1)) * UNITS[m.group(2) or "pt"]


def wxh(text):
    w, _, h = text.lower().partition("x")
    return float(w), float(h)


class Checks:
    def __init__(self):
        self.rows = []

    def add(self, name, ok, got):
        self.rows.append({"check": name, "ok": bool(ok), "got": got})

    def done(self, extra):
        failed = [r for r in self.rows if not r["ok"]]
        print(json.dumps(dict(extra, checks=self.rows, ok=not failed), indent=1, ensure_ascii=False))
        return 1 if failed else 0


def cmd_doc(a):
    path = os.path.abspath(a.file)
    meta = info(path)
    s = Session(os.path.dirname(path))
    try:
        s.tool("open_file", {"path": path})
        layers = s.tree()
        styles = s.tool("inspect_document", {"depth": 0}).get("styles") or []
    finally:
        s.close()
    top = [n for n in layers if n["parent"] is None]
    style_names = {x.get("id"): x.get("name") for x in styles}
    texts = [{"name": n["name"], "frame": n["top"], "text": n["node"].get("characters"),
              "style": style_names.get((n["node"].get("styles") or {}).get("text"))}
             for n in layers if n["type"] == "TEXT"]
    comps = {n["id"]: n["name"] for n in layers if n["type"] in ("COMPONENT", "COMPONENT_SET")}
    sets = {n["id"]: comps.get(n["parent"]) for n in layers
            if n["type"] == "COMPONENT" and n["parent"] in comps}  # variant -> its set's name
    instances = []
    for n in layers:
        if n["type"] == "INSTANCE":
            main = n["node"].get("mainComponent")
            instances.append({"name": n["name"], "frame": n["top"], "component": sets.get(main) or comps.get(main),
                              "variant": comps.get(main) if main in sets else None})
    summary = {
        "file": path,
        "topLevel": [{"name": n["name"], "type": n["type"], "size": [n["node"].get("width"), n["node"].get("height")],
                      "page": n["page"]} for n in top],
        "texts": texts, "components": sorted(set(comps.values())), "instances": instances,
        "styles": [x.get("name") for x in styles], "notes": meta.get("notes", []),
        "missingFonts": meta.get("missingFonts", []),
    }
    c = Checks()
    if a.frames is not None:
        c.add("frames == %d" % a.frames, len(top) == a.frames, len(top))
    for f in a.frame or []:
        name, _, size = f.partition("=")
        hit = [n for n in top if n["name"] == name]
        got = [(n["node"].get("width"), n["node"].get("height")) for n in hit]
        c.add("frame " + f, any(g == wxh(size) for g in got), got)
    for t in a.text or []:
        name, _, want = t.partition("=")
        frame, _, leaf = name.rpartition("/") if "/" in name else ("", "", name)
        got = [x["text"] for x in texts if x["name"] == leaf and (not frame or x["frame"] == frame)]
        c.add("text " + t, want in got, got)
    for t in a.has_text or []:
        c.add("has text %r" % t, any(t in (x["text"] or "") for x in texts), None)
    names = {n["name"] for n in layers}
    for n in a.names or []:
        c.add("layer %r" % n, n in names, None)
    for n in a.component or []:
        c.add("component %r" % n, n in comps.values(), sorted(set(comps.values())))
    for spec in a.instance or []:
        comp, _, frame = spec.partition("@")
        ok = any(comp in (i["component"], i["variant"]) and (not frame or i["frame"] == frame) for i in instances)
        c.add("instance " + spec, ok, instances)
    for n in a.auto_layout or []:
        modes = [(x["node"].get("layout") or {}).get("mode") for x in layers if x["name"] == n]
        c.add("auto layout %r" % n, any(m in ("horizontal", "vertical", "grid") for m in modes), modes)
    for n in a.style or []:
        c.add("style %r" % n, n in summary["styles"], summary["styles"])
    for name in a.fill or []:
        frame, _, leaf = name.rpartition("/") if "/" in name else ("", "", name)
        got = [(x["node"].get("sizing") or {}).get("horizontal") for x in layers
               if x["name"] == leaf and (not frame or x["top"] == frame) and x["parent"] is not None]
        c.add("fills width %r" % name, bool(got) and all(g == "fill" for g in got), got)
    for t in a.text_style or []:
        chars, _, style = t.rpartition("=")
        got = [x["style"] for x in texts if x["text"] == chars]
        c.add("text style " + t, bool(got) and all(g == style for g in got), got)
    if a.no_notes:
        c.add("no import notes", not summary["notes"], summary["notes"])
    if a.fonts_ok:
        c.add("no missing fonts", not summary["missingFonts"], summary["missingFonts"])
    return c.done(summary)


def png_size(path):
    with open(path, "rb") as fh:
        head = fh.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def pdf_info(path):
    data = open(path, "rb").read()
    pages = len(re.findall(rb"/Type\s*/Page(?![s\w])", data))
    boxes = {}
    for name in ("MediaBox", "BleedBox", "TrimBox"):
        m = re.search(rb"/" + name.encode() + rb"\s*\[\s*([-\d.\s]+)\]", data)
        if m:
            boxes[name] = [float(x) for x in m.group(1).split()]
    return pages, boxes


def cmd_files(a):
    paths = []
    for p in a.paths:
        if os.path.isdir(p):
            paths += sorted(q for q in glob.glob(os.path.join(p, "**", "*"), recursive=True) if os.path.isfile(q))
        else:
            paths.append(p)
    if a.ext:
        paths = [p for p in paths if p.lower().endswith("." + a.ext.lower())]
    c = Checks()
    files = []
    for p in paths:
        row = {"file": p}
        ext = p.lower().rsplit(".", 1)[-1]
        if ext == "png":
            row["px"] = png_size(p)
        elif ext == "svg":
            try:
                root = ET.parse(p).getroot()
                row["svg"] = root.tag.endswith("svg")
                row["textElements"] = sum(1 for e in root.iter() if e.tag.endswith("}text"))
            except ET.ParseError as e:
                row["svg"] = False
                row["error"] = str(e)
        elif ext == "pdf":
            row["pages"], row["boxes"] = pdf_info(p)
        files.append(row)
    if a.count is not None:
        c.add("count == %d" % a.count, len(files) == a.count, len(files))
    if a.px:
        want = sorted(tuple(int(v) for v in wxh(x)) for x in a.px)
        got = sorted(tuple(f["px"]) for f in files if f.get("px"))
        ok = got == want if len(want) == len(got) else (len(want) == 1 and all(g == want[0] for g in got) and got)
        c.add("px " + " ".join(a.px), bool(ok), got)
    if a.svg:
        c.add("well-formed SVG", files and all(f.get("svg") for f in files), [f.get("svg") for f in files])
    for f in files:
        if "pages" not in f:
            continue
        name = os.path.basename(f["file"])
        b = f["boxes"]
        if a.pdf_pages is not None:
            c.add("%s pages == %d" % (name, a.pdf_pages), f["pages"] == a.pdf_pages, f["pages"])
        trim = b.get("TrimBox") or b.get("MediaBox")
        if a.trim:
            got = (round(trim[2] - trim[0], 1), round(trim[3] - trim[1], 1))
            c.add("%s trim %s pt" % (name, a.trim), got == wxh(a.trim), got)
        if a.bleed:
            want = length_pt(a.bleed)
            bl = b.get("BleedBox")
            got = [round(x, 2) for x in (trim[0] - bl[0], trim[1] - bl[1], bl[2] - trim[2], bl[3] - trim[3])] if bl else None
            c.add("%s bleed %s" % (name, a.bleed), bool(got) and all(abs(g - want) < 0.3 for g in got), got)
        if a.marks:
            m, bl = b.get("MediaBox"), b.get("BleedBox") or trim
            c.add("%s marks margin" % name, m[2] - m[0] > bl[2] - bl[0] + 1, {"media": m, "bleed": bl})
    return c.done({"files": files})


def digest(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def cmd_hash(a):
    found = {}
    for p in sorted(glob.glob(os.path.join(a.dir, "**", "*"), recursive=True)):
        if os.path.isfile(p):
            found[os.path.relpath(p, a.dir)] = digest(p)
    if not a.compare:
        print(json.dumps(found, indent=1))
        return 0
    want = json.load(open(a.compare))
    changed = sorted(k for k in want if found.get(k) != want[k])
    added = sorted(k for k in found if k not in want)
    print(json.dumps({"changed_or_missing": changed, "added": added, "ok": not changed and not added}, indent=1))
    return 1 if changed or added else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)
    d = sub.add_parser("doc")
    d.add_argument("file")
    d.add_argument("--frames", type=int)
    d.add_argument("--frame", nargs="+")
    d.add_argument("--text", nargs="+")
    d.add_argument("--has-text", nargs="+")
    d.add_argument("--names", nargs="+")
    d.add_argument("--component", nargs="+")
    d.add_argument("--instance", nargs="+")
    d.add_argument("--auto-layout", nargs="+")
    d.add_argument("--style", nargs="+")
    d.add_argument("--text-style", nargs="+")
    d.add_argument("--fill", nargs="+")
    d.add_argument("--no-notes", action="store_true")
    d.add_argument("--fonts-ok", action="store_true")
    f = sub.add_parser("files")
    f.add_argument("paths", nargs="+")
    f.add_argument("--ext")
    f.add_argument("--count", type=int)
    f.add_argument("--px", nargs="+")
    f.add_argument("--svg", action="store_true")
    f.add_argument("--pdf-pages", type=int)
    f.add_argument("--trim")
    f.add_argument("--bleed")
    f.add_argument("--marks", action="store_true")
    h = sub.add_parser("hash")
    h.add_argument("dir")
    h.add_argument("--compare")
    a = ap.parse_args()
    return {"doc": cmd_doc, "files": cmd_files, "hash": cmd_hash}[a.mode](a)


if __name__ == "__main__":
    sys.exit(main())
