#!/usr/bin/env python3
"""Read-back checks for VectorCraft work. Prints JSON; exits 1 if any check fails.

    vc_verify.py doc FILE [--artboards N] [--size WxH ...] [--min-kind Type=1 ...]
                 [--text NAME=CONTENT ...] [--has-text STR ...] [--color #hex ...]
                 [--no-color #hex ...] [--no-import-warnings] [--fonts-ok]
        --size lists the artboard sizes in order (document units).
        --text/--has-text/--color need a headless session (slower, one per call).
    vc_verify.py files DIR --ext svg [--count N] [--px WxH ...] [--no-svg-text]
                 [--max-decimals N] [--pdf-pages N]
        --px lists expected raster sizes; with one value every file must match it.
    vc_verify.py hash DIR [--compare manifest.json]
        Without --compare: print a sha256 manifest (save it before a batch).
"""
import argparse
import hashlib
import json
import os
import re
import struct
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vclib import Session, info  # noqa: E402


def check(results, name, ok, detail=""):
    results.append({"check": name, "ok": bool(ok), "detail": detail})


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", head[16:24])
    return None


def raster_size(path):
    size = png_size(path)
    if size:
        return size
    out = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", path],
                         capture_output=True, text=True).stdout
    nums = re.findall(r"pixel(?:Width|Height): (\d+)", out)
    return tuple(int(n) for n in nums) if len(nums) == 2 else None


def pdf_pages(path):
    out = subprocess.run(["pdfinfo", path], capture_output=True, text=True).stdout
    m = re.search(r"Pages:\s+(\d+)", out)
    if m:
        return int(m.group(1))
    data = open(path, "rb").read()
    return len(re.findall(rb"/Type\s*/Page[^s]", data)) or None


def cmd_doc(a):
    res = []
    d = info(a.file)
    abs_ = d["artboards"]
    if a.artboards is not None:
        check(res, "artboards == %d" % a.artboards, len(abs_) == a.artboards, len(abs_))
    if a.size:
        got = ["%gx%g" % (ab["rect"][2], ab["rect"][3]) for ab in abs_]
        want = [s.lower() for s in a.size]
        check(res, "artboard sizes", got[:len(want)] == want, got)
    for spec in a.min_kind or []:
        kind, _, n = spec.partition("=")
        check(res, "%s >= %s" % (kind, n), d["kinds"].get(kind, 0) >= int(n or 1), d["kinds"])
    if a.no_import_warnings:
        check(res, "no import warnings", not d["warnings"], d["warnings"])
    if a.fonts_ok:
        bad = [f["family"] for f in d["fonts"] if f.get("missing") or f.get("status") != "exact"]
        check(res, "fonts resolved", not bad, bad)
    if a.text or a.has_text or a.color or a.no_color:
        path = os.path.realpath(a.file)
        s = Session(os.path.dirname(path))
        try:
            s.tool("open_file", {"path": path})
            for spec in a.text or []:
                name, _, want = spec.partition("=")
                m = s.find(name=name, kind="Type")
                got = s.cmd("document.node", {"id": m[0]["id"], "summary": True}).get("text") if m else None
                check(res, "text %s" % name, got == want, got)
            for want in a.has_text or []:
                check(res, "has text %r" % want, s.find(text=want), [m["name"] for m in s.find(text=want)])
            if a.color or a.no_color:
                s.cmd("select.all")
                used = sorted(c["hex"].lower() for c in s.cmd("recolor.colors").get("colors", []))
                for c in a.color or []:
                    check(res, "uses %s" % c, c.lower() in used, used)
                for c in a.no_color or []:
                    check(res, "does not use %s" % c, c.lower() not in used, used)
        finally:
            s.close()
    summary = {"artboards": [[ab["name"]] + ab["rect"][2:] for ab in abs_], "kinds": d["kinds"],
               "colorMode": d["info"]["colorMode"], "units": d["info"]["units"],
               "fonts": ["%s: %s" % (f["family"], f["status"]) for f in d["fonts"]],
               "importWarnings": d["warnings"]}
    return res, summary


def cmd_files(a):
    res = []
    files = sorted(os.path.join(a.dir, f) for f in os.listdir(a.dir)
                   if f.lower().endswith("." + a.ext.lower().strip(".")))
    if a.count is not None:
        check(res, "count == %d" % a.count, len(files) == a.count, [os.path.basename(f) for f in files])
    if a.px:
        sizes = [raster_size(f) for f in files]
        got = ["%dx%d" % s if s else "?" for s in sizes]
        want = a.px * len(files) if len(a.px) == 1 else a.px
        check(res, "pixel sizes", got == [w.lower() for w in want], dict(zip(map(os.path.basename, files), got)))
    for f in files:
        name = os.path.basename(f)
        if a.ext.lower().strip(".") in ("svg",):
            text = open(f, encoding="utf-8", errors="replace").read()
            if a.no_svg_text:
                check(res, "%s: no <text>" % name, "<text" not in text, text.count("<text"))
            if a.max_decimals is not None:
                long_ = re.findall(r"\d+\.(\d{%d,})" % (a.max_decimals + 1), text)
                check(res, "%s: <= %d decimals" % (name, a.max_decimals), not long_, len(long_))
        if a.pdf_pages is not None:
            check(res, "%s: %d pages" % (name, a.pdf_pages), pdf_pages(f) == a.pdf_pages, pdf_pages(f))
    return res, {"files": [os.path.basename(f) for f in files]}


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd_hash(a):
    manifest = {}
    for dirpath, _, names in os.walk(a.dir):
        for n in names:
            p = os.path.join(dirpath, n)
            manifest[os.path.relpath(p, a.dir)] = sha(p)
    if not a.compare:
        return None, manifest
    old = json.load(open(a.compare))
    old = old.get("manifest", old)
    res = []
    changed = [k for k in old if manifest.get(k) != old[k]]
    added = [k for k in manifest if k not in old]
    check(res, "inputs unchanged", not changed, changed)
    check(res, "no new files in input", not added, added)
    return res, {}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)
    d = sub.add_parser("doc")
    d.add_argument("file")
    d.add_argument("--artboards", type=int)
    d.add_argument("--size", nargs="+")
    d.add_argument("--min-kind", nargs="+")
    d.add_argument("--text", nargs="+")
    d.add_argument("--has-text", nargs="+")
    d.add_argument("--color", nargs="+")
    d.add_argument("--no-color", nargs="+")
    d.add_argument("--no-import-warnings", action="store_true")
    d.add_argument("--fonts-ok", action="store_true")
    f = sub.add_parser("files")
    f.add_argument("dir")
    f.add_argument("--ext", required=True)
    f.add_argument("--count", type=int)
    f.add_argument("--px", nargs="+")
    f.add_argument("--no-svg-text", action="store_true")
    f.add_argument("--max-decimals", type=int)
    f.add_argument("--pdf-pages", type=int)
    h = sub.add_parser("hash")
    h.add_argument("dir")
    h.add_argument("--compare")
    a = ap.parse_args()

    res, extra = {"doc": cmd_doc, "files": cmd_files, "hash": cmd_hash}[a.mode](a)
    if res is None:  # plain manifest
        print(json.dumps(extra, indent=1))
        return 0
    ok = all(r["ok"] for r in res)
    print(json.dumps({"ok": ok, "checks": res, **extra}, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
