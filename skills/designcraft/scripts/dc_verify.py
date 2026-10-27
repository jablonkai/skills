#!/usr/bin/env python3
"""Read a DesignCraft document, PDF or PNG back and check it. Prints JSON; exit 1 on a failed check.

  dc_verify.py doc F.designcraft [--pages 4] [--size A4|595x842] [--no-overset]
      [--style 'Body:size=12' 'Body:leading=14' 'Body:spaceAfter=6']
      [--story-style 'The ridge trail=Body']      # story containing the text uses the style
      [--thread 'The ridge trail=2,3']            # story containing the text has frames on pages
      [--image photo1.jpg@1 photo2.jpg@4] [--parent-text 'Northwind Trails'] [--page-number]
      [--placeholders name title] [--data attendees.csv] [--fonts-ok]
  dc_verify.py pdf F.pdf [--x4] [--pages 4] [--size A4] [--bleed 3mm] [--marks]
      [--text 'Ada Lovelace' …] [--once] [--page-numbers]
  dc_verify.py png F.png [--size 1191x1684] [--tolerance 4]
  dc_verify.py hash PATH… [--compare manifest.json]   # write or compare sha256s

Without check flags `doc` prints a summary: pages, size, parents, styles, stories (preview,
overset, frame pages, paragraph styles) and placed images per page. Pages are 1-based.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys

from dclib import PAGE_MARKER, doc_json, inspect, links, run_cmds, validate_pdf

SIZES = {"A4": (595.276, 841.89), "A5": (419.528, 595.276), "A3": (841.89, 1190.551),
         "LETTER": (612, 792), "LEGAL": (612, 1008), "TABLOID": (792, 1224)}
UNITS = {"pt": 1.0, "mm": 72 / 25.4, "cm": 72 / 2.54, "in": 72.0}


def length(v):
    m = re.fullmatch(r"([\d.]+)\s*(pt|mm|cm|in)?", v.strip())
    return float(m.group(1)) * UNITS[m.group(2) or "pt"]


def size(v):
    if v.upper() in SIZES:
        return SIZES[v.upper()]
    w, h = v.lower().split("x")
    return length(w), length(h)


class Checks:
    def __init__(self):
        self.items = []

    def add(self, name, ok, got):
        self.items.append({"check": name, "ok": bool(ok), "got": got})

    def done(self, summary):
        failed = [c for c in self.items if not c["ok"]]
        print(json.dumps({"ok": not failed, "checks": self.items, "summary": summary}, indent=2,
                         ensure_ascii=False))
        sys.exit(1 if failed else 0)


def page_of(insp, spread_idx, x0):
    for sp in insp["spreads"]:
        if sp["index"] == spread_idx:
            for pg in sp["pages"]:
                if pg["bounds"][0] - 1 <= x0 < pg["bounds"][2] + 1:
                    return pg["index"] + 1
    return None


def doc_summary(path):
    insp, dj = inspect(path), doc_json(path)
    frame_page = {}
    for sp in insp["spreads"]:
        for it in sp["items"]:
            frame_page[it["id"]] = page_of(insp, sp["index"], it["bounds"][0])
    stories = []
    parent_frames = {it["id"] for par in dj["parents"] for it in par.get("items", [])}
    for st in insp["stories"]:
        model = dj["stories"][str(st["id"])]
        stories.append({"id": st["id"], "preview": model["text"][:60].replace(PAGE_MARKER, "{page}"),
                        "overset": st["overset"],
                        "pages": sorted({frame_page.get(f) for f in st["frames"] if f in frame_page} - {None}),
                        "onParent": any(f in parent_frames for f in st["frames"]),
                        "paragraphStyles": sorted({p.get("style") for p in model["paras"]})})
    images = [{"name": l["name"], "status": l["status"], "pages": [int(u["page"]) for u in l["uses"]]}
              for l in links(path) if "asset" in l]
    styles = {s["name"]: dict(s.get("chars", {}), **s.get("para", {}))
              for s in dj["styles"]["paragraph"] if not s["name"].startswith("[")}
    srcs = [s.get("name") for s in (dj.get("dataMerge") or {}).get("sources") or []]
    missing = ["%s %s → %s" % (f["family"], f["style"], f.get("resolvedFamily"))
               for f in run_cmds(path, "font.list") or [] if f.get("missing") or f.get("styleMissing")]
    return {"pages": insp["pageCount"], "size": [round(insp["settings"]["pageWidth"], 2),
            round(insp["settings"]["pageHeight"], 2)], "facingPages": insp["settings"]["facingPages"],
            "parents": [p["label"] for p in insp["parents"]], "paragraphStyles": styles,
            "characterStyles": [c for c in insp["characterStyles"] if not c.startswith("[")],
            "stories": stories, "images": images, "dataSources": srcs,
            "missingFonts": missing}


def cmd_doc(a):
    c, s = Checks(), doc_summary(a.file)
    if a.pages is not None:
        c.add("pages == %d" % a.pages, s["pages"] == a.pages, s["pages"])
    if a.size:
        w, h = size(a.size)
        c.add("size %s" % a.size, abs(s["size"][0] - w) < 1 and abs(s["size"][1] - h) < 1, s["size"])
    if a.no_overset:
        bad = [st["id"] for st in s["stories"] if st["overset"]]
        c.add("no overset story", not bad, bad)
    for spec in a.style or []:
        name, kv = spec.split(":", 1)
        key, want = kv.split("=", 1)
        got = s["paragraphStyles"].get(name, {}).get(key)
        if isinstance(got, dict) and "value" in got:  # leading {kind: points, value}
            got = got["value"]
        try:
            ok = got is not None and abs(float(got) - float(want)) < 0.01
        except (TypeError, ValueError):
            ok = str(got) == want
        c.add("style %s" % spec, ok, got)
    for spec in a.story_style or []:
        probe, style = spec.rsplit("=", 1)
        hit = [st for st in s["stories"] if probe in doc_json_text(a.file, st["id"])]
        c.add("story with %r uses %s" % (probe, style), hit and style in hit[0]["paragraphStyles"],
              hit[0]["paragraphStyles"] if hit else "no such story")
    for spec in a.thread or []:
        probe, pages = spec.rsplit("=", 1)
        want = {int(p) for p in pages.split(",")}
        hit = [st for st in s["stories"] if probe in doc_json_text(a.file, st["id"])]
        c.add("story with %r has frames on pages %s" % (probe, sorted(want)),
              hit and want <= set(hit[0]["pages"]) and not hit[0]["overset"],
              {"pages": hit[0]["pages"], "overset": hit[0]["overset"]} if hit else "no such story")
    for spec in a.image or []:
        name, page = spec.rsplit("@", 1)
        ok = any(i["name"] == name and int(page) in i["pages"] and i["status"] in ("ok", "embedded")
                 for i in s["images"])
        c.add("image %s on page %s" % (name, page), ok, s["images"])
    if a.parent_text:
        texts = [st["preview"] for st in s["stories"] if st["onParent"]]
        c.add("parent holds %r" % a.parent_text, any(a.parent_text in t for t in texts), texts)
    if a.page_number:
        texts = [st["preview"] for st in s["stories"] if st["onParent"]]
        c.add("parent holds a page-number marker", any("{page}" in t for t in texts), texts)
    if a.placeholders:
        dj = doc_json(a.file)
        found = set()
        for st in dj["stories"].values():
            found |= set(re.findall(r"<<([^<>]+)>>", st["text"]))
        c.add("placeholders %s" % a.placeholders, set(a.placeholders) <= found, sorted(found))
    if a.fonts_ok:
        c.add("no missing fonts", not s["missingFonts"], s["missingFonts"])
    if a.data:
        c.add("data source %s" % a.data, a.data in s["dataSources"], s["dataSources"])
    c.done(s)


def doc_json_text(path, story_id, _cache={}):
    if path not in _cache:
        _cache[path] = doc_json(path)
    return _cache[path]["stories"][str(story_id)]["text"]


def poppler(tool, *args):
    exe = shutil.which(tool)
    if not exe:
        sys.exit("%s not found (brew install poppler)" % tool)
    return subprocess.run([exe] + list(args), capture_output=True, text=True).stdout


def cmd_pdf(a):
    c = Checks()
    info = poppler("pdfinfo", "-box", a.file)
    boxes = {}
    for name in ("MediaBox", "BleedBox", "TrimBox"):
        m = re.search(name + r":\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)", info)
        if m:
            boxes[name] = [float(x) for x in m.groups()]
    pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
    trim = boxes.get("TrimBox") or boxes["MediaBox"]
    s = {"pages": pages, "trim": [round(trim[2] - trim[0], 2), round(trim[3] - trim[1], 2)], "boxes": boxes}
    if a.x4:
        v = validate_pdf(a.file)
        s["validate"] = v
        c.add("validate-pdf PDF/X-4", v.get("valid") and v.get("standard") == "PDF/X-4", v.get("issues"))
    if a.pages is not None:
        c.add("pages == %d" % a.pages, pages == a.pages, pages)
    if a.size:
        w, h = size(a.size)
        c.add("trim size %s" % a.size, abs(s["trim"][0] - w) < 1 and abs(s["trim"][1] - h) < 1, s["trim"])
    if a.bleed:
        b, bl = length(a.bleed), boxes.get("BleedBox")
        got = [trim[0] - bl[0], trim[1] - bl[1], bl[2] - trim[2], bl[3] - trim[3]] if bl else None
        c.add("bleed %s" % a.bleed, got and all(abs(x - b) < 0.6 for x in got),
              [round(x, 2) for x in got] if got else "no BleedBox")
    if a.marks:
        m, bl = boxes["MediaBox"], boxes.get("BleedBox") or trim
        c.add("media box larger than bleed (marks)", m[2] - m[0] > bl[2] - bl[0] + 2, boxes)
    text = poppler("pdftotext", "-layout", a.file, "-")
    flat = re.sub(r"\s+", " ", text)
    for t in a.text or []:
        n = flat.count(t)
        c.add("text %r %s" % (t, "once" if a.once else "present"), n == 1 if a.once else n >= 1, n)
    if a.page_numbers:
        got = []
        for p in range(1, pages + 1):
            pt = poppler("pdftotext", "-f", str(p), "-l", str(p), a.file, "-")
            got.append(bool(re.search(r"(?<!\d)%d(?!\d)" % p, pt)))
        c.add("each page shows its own number", all(got), got)
    c.done(s)


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        sys.exit("%s is not a PNG" % path)
    return struct.unpack(">II", head[16:24])


def cmd_png(a):
    c = Checks()
    w, h = png_size(a.file)
    if a.size:
        ww, wh = (float(x) for x in a.size.lower().split("x"))
        c.add("size ~%s" % a.size, abs(w - ww) <= a.tolerance and abs(h - wh) <= a.tolerance, [w, h])
    c.done({"size": [w, h]})


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd_hash(a):
    got = {p: sha(p) for p in a.paths}
    if not a.compare:
        print(json.dumps(got, indent=2))
        return
    if not os.path.exists(a.compare):
        json.dump(got, open(a.compare, "w"), indent=2)
        print(json.dumps({"written": a.compare, "files": got}, indent=2))
        return
    c, old = Checks(), json.load(open(a.compare))
    for p, h in got.items():
        c.add("unchanged %s" % p, old.get(p) == h, h[:12])
    c.done({})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("doc")
    d.add_argument("file")
    d.add_argument("--pages", type=int)
    d.add_argument("--size")
    d.add_argument("--no-overset", action="store_true")
    d.add_argument("--style", nargs="+")
    d.add_argument("--story-style", nargs="+")
    d.add_argument("--thread", nargs="+")
    d.add_argument("--image", nargs="+")
    d.add_argument("--parent-text")
    d.add_argument("--page-number", action="store_true")
    d.add_argument("--placeholders", nargs="+")
    d.add_argument("--data")
    d.add_argument("--fonts-ok", action="store_true")
    p = sub.add_parser("pdf")
    p.add_argument("file")
    p.add_argument("--x4", action="store_true")
    p.add_argument("--pages", type=int)
    p.add_argument("--size")
    p.add_argument("--bleed")
    p.add_argument("--marks", action="store_true")
    p.add_argument("--text", nargs="+")
    p.add_argument("--once", action="store_true")
    p.add_argument("--page-numbers", action="store_true")
    g = sub.add_parser("png")
    g.add_argument("file")
    g.add_argument("--size")
    g.add_argument("--tolerance", type=float, default=4)
    h = sub.add_parser("hash")
    h.add_argument("paths", nargs="+")
    h.add_argument("--compare")
    a = ap.parse_args()
    {"doc": cmd_doc, "pdf": cmd_pdf, "png": cmd_png, "hash": cmd_hash}[a.cmd](a)


if __name__ == "__main__":
    main()
