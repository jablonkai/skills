#!/usr/bin/env python3
"""Read a CADCraft result back and check it. Prints JSON; exits 1 on any failed check.

    cc_verify.py doc FILE.dxf|dwg [checks]
        --layer NAME ...           layers that must exist
        --count TYPE=N ...         entities of TYPE (as `info` counts them: Line, Circle,
                                   Polyline, Dimension, Text, MText, Hatch, "Block Reference"…);
                                   TYPE>=N for a minimum
        --on-layer LAYER=N ...     entities on LAYER (N=0 for "empty"); LAYER>=N for a minimum
        --type-on TYPE=LAYER ...   every entity of TYPE is on LAYER
        --attr TAG=VALUE ...       some block reference has this attribute value
        --text SUBSTRING ...       some text/mtext/attribute contains it
    ezdxf checks (independent of CADCraft; DXF only; need `import ezdxf`):
        --units mm|in|m|cm|ft      $INSUNITS
        --circles R=N ...          N circles of radius R (±0.001)
        --size LAYER=WxH ...       bounding box of LAYER's entities (±0.01)

    cc_verify.py files DIR --ext png [--count N] [--px 2400x1600] [--pdf-pages 1] [--svg]
    cc_verify.py hash DIR [--compare manifest.json]    SHA-256 of every file (vs a manifest)
"""
import argparse
import hashlib
import json
import os
import re
import struct
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cclib import Session, ToolError, info  # noqa: E402

UNITS = {"in": 1, "ft": 2, "mm": 4, "cm": 5, "m": 6}


class Checks:
    def __init__(self):
        self.items = []

    def add(self, name, ok, got):
        self.items.append({"check": name, "ok": bool(ok), "got": got})

    def report(self, extra=None):
        failed = [c for c in self.items if not c["ok"]]
        out = {"ok": not failed, "failed": len(failed), "checks": self.items}
        out.update(extra or {})
        print(json.dumps(out, indent=1))
        return 0 if not failed else 1


def kv(text):
    m = re.match(r"^(.+?)(>=|=)(.*)$", text)
    if not m:
        sys.exit("expected KEY=VALUE or KEY>=VALUE: %s" % text)
    return m.group(1), m.group(2), m.group(3)


def num(spec, n):
    if not n.isdigit():
        sys.exit("expected a count after = in %s (e.g. LAYER=3); to check a type's layer use --type-on TYPE=LAYER" % spec)
    return int(n)


def cmp(op, got, want):
    return got >= want if op == ">=" else got == want


def all_entities(s, **filt):
    out, offset = [], 0
    while True:
        res = s.tool("query_entities", dict(filt, limit=500, offset=offset))
        out += res.get("entities", [])
        offset += res.get("returned", 0)
        if not res.get("returned") or offset >= res.get("count", 0):
            return out


def doc(a):
    c = Checks()
    d = info(a.file)
    counts = d.get("counts", {})
    layers = [l["name"] for l in d.get("layers", [])]
    for name in a.layer:
        c.add("layer %s exists" % name, name in layers, layers)
    for spec in a.count:
        t, op, n = kv(spec)
        c.add("count %s%s%s" % (t, op, n), cmp(op, counts.get(t, 0), num(spec, n)), counts.get(t, 0))

    if a.on_layer or a.type_on or a.attr or a.text:
        s = Session()
        try:
            s.tool("open", {"path": os.path.abspath(a.file)})
            for spec in a.on_layer:
                layer, op, n = kv(spec)
                got = len(all_entities(s, layer=layer))
                c.add("on layer %s%s%s" % (layer, op, n), cmp(op, got, num(spec, n)), got)
            for spec in a.type_on:
                t, _, layer = kv(spec)
                ents = [e for e in all_entities(s) if e.get("type") == t]
                wrong = sorted({e.get("layer") for e in ents} - {layer})
                c.add("every %s on %s" % (t, layer), ents and not wrong,
                      {"n": len(ents), "other_layers": wrong})
            if a.attr:
                ex = s.cmd("eattext", {"combine": False})
                cols = ex.get("columns", [])
                rows = [dict(zip(cols, r)) for r in ex.get("rows", [])]
                for spec in a.attr:
                    tag, _, val = kv(spec)
                    got = [r.get(tag.upper()) for r in rows if tag.upper() in r]
                    c.add("attribute %s=%s" % (tag, val), val in got, got)
            for sub in a.text:
                res = s.tool("find_text", {"contains": sub, "limit": 5})
                c.add("text contains %r" % sub, res.get("count", 0) > 0,
                      [t.get("text") for t in res.get("texts", [])])
        except ToolError as e:
            c.add("session", False, str(e))
        finally:
            s.close()

    if a.units or a.circles or a.size:
        try:
            import ezdxf
            from ezdxf import bbox
        except ImportError:
            c.add("ezdxf available", False, "pip install ezdxf (see SKILL.md › Setup)")
            return c.report()
        x = ezdxf.readfile(a.file)
        msp = x.modelspace()
        if a.units:
            got = x.header.get("$INSUNITS")
            c.add("units %s" % a.units, got == UNITS[a.units], got)
        for spec in a.circles:
            r, _, n = kv(spec)
            got = sum(1 for e in msp.query("CIRCLE") if abs(e.dxf.radius - float(r)) <= 1e-3)
            c.add("%s circles r=%s (ezdxf)" % (n, r), got == num(spec, n), got)
        for spec in a.size:
            layer, _, wh = kv(spec)
            w, h = [float(v) for v in wh.lower().split("x")]
            ents = msp.query('*[layer=="%s"]' % layer)
            box = bbox.extents(ents)
            got = [round(box.size.x, 4), round(box.size.y, 4)] if box.has_data else None
            c.add("layer %s size %sx%s (ezdxf)" % (layer, w, h),
                  got and abs(got[0] - w) <= 0.01 and abs(got[1] - h) <= 0.01, got)
    return c.report({"file": a.file, "counts": counts, "extents": d.get("extents")})


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def pdf_pages(path):
    with open(path, "rb") as f:
        data = f.read()
    if not data.startswith(b"%PDF"):
        return None
    return len(re.findall(rb"/Type\s*/Page(?![A-Za-z])", data))  # not /Pages, /PageLabel


def files(a):
    c = Checks()
    ext = "." + a.ext.lstrip(".").lower()
    found = sorted(os.path.join(d, n) for d, _, ns in os.walk(a.dir) for n in ns if n.lower().endswith(ext))
    if a.count is not None:
        c.add("%d %s files" % (a.count, ext), len(found) == a.count, len(found))
    for p in found:
        if ext == ".png":
            size = png_size(p)
            c.add("%s is PNG" % p, size is not None, size)
            if a.px and size:
                c.add("%s is %s px" % (p, a.px), "%dx%d" % size == a.px, "%dx%d" % size)
        elif ext == ".pdf":
            n = pdf_pages(p)
            c.add("%s is PDF" % p, n is not None, n)
            if a.pdf_pages is not None and n is not None:
                c.add("%s has %d page(s)" % (p, a.pdf_pages), n == a.pdf_pages, n)
        elif ext == ".svg" or a.svg:
            try:
                root = ET.parse(p).getroot()
                c.add("%s parses as SVG" % p, root.tag.endswith("svg"), root.tag)
            except ET.ParseError as e:
                c.add("%s parses as SVG" % p, False, str(e))
        elif ext == ".dwg":
            with open(p, "rb") as f:
                magic = f.read(6)
            c.add("%s is DWG" % p, magic.startswith(b"AC10"), magic.decode("latin-1"))
        elif ext == ".dxf":
            try:
                info(p)
                c.add("%s opens" % p, True, "ok")
            except RuntimeError as e:
                c.add("%s opens" % p, False, str(e))
    return c.report({"files": found})


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def hashes(a):
    now = {os.path.relpath(os.path.join(d, n), a.dir): sha(os.path.join(d, n))
           for d, _, ns in os.walk(a.dir) for n in sorted(ns)}
    if not a.compare:
        print(json.dumps(now, indent=1))
        return 0
    with open(a.compare) as f:
        then = json.load(f)
    c = Checks()
    for rel, digest in then.items():
        c.add("%s unchanged" % rel, now.get(rel) == digest, "same" if now.get(rel) == digest else "changed/missing")
    added = sorted(set(now) - set(then))
    c.add("no new files in %s" % a.dir, not added, added)
    return c.report()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("doc")
    p.add_argument("file")
    for flag in ("--layer", "--count", "--on-layer", "--type-on", "--attr", "--text", "--circles", "--size"):
        p.add_argument(flag, nargs="+", action="extend", default=[])
    p.add_argument("--units", choices=sorted(UNITS))
    p = sub.add_parser("files")
    p.add_argument("dir")
    p.add_argument("--ext", required=True)
    p.add_argument("--count", type=int)
    p.add_argument("--px")
    p.add_argument("--pdf-pages", type=int)
    p.add_argument("--svg", action="store_true")
    p = sub.add_parser("hash")
    p.add_argument("dir")
    p.add_argument("--compare")
    a = ap.parse_args()
    return {"doc": doc, "files": files, "hash": hashes}[a.mode](a)


if __name__ == "__main__":
    sys.exit(main())
