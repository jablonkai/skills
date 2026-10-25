#!/usr/bin/env python3
"""Read-back checks for PhotoCraft results. Prints JSON; exit 1 if any check fails.

Usage:
  pc_verify.py doc FILE [--size WxH] [--mode rgb] [--depth 8]
                        [--has NAME]... [--visible NAME]... [--hidden NAME]...
                        [--text NAME=TEXT]... [--effect NAME=KIND]... [--order A,B,...]
      Checks a layered document (.pcraft/.psd/.tif) through `photocraft-cli info`.
      --order lists layer names top to bottom (others may sit in between).
  pc_verify.py files DIR [--count N] [--ext webp] [--size WxH] [--long-edge N]
                         [--webp lossy|lossless]
      Checks every image file in DIR (not recursive).
  pc_verify.py hash DIR [--compare MANIFEST.json]
      Without --compare prints a sha256 manifest of DIR; with it, fails on any
      changed, missing or added file. Snapshot inputs before a batch, compare after.
"""

import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pclib import PcError, die, find_layer, info, walk  # noqa: E402

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".psd", ".psb",
              ".pcraft", ".exr", ".tga", ".dpx", ".gif", ".bmp"}


class Report(object):
    def __init__(self):
        self.checks = []

    def add(self, name, passed, detail=""):
        self.checks.append({"check": name, "passed": bool(passed), "detail": detail})

    def finish(self):
        ok = all(c["passed"] for c in self.checks)
        print(json.dumps({"ok": ok, "checks": self.checks}, indent=2, ensure_ascii=False))
        sys.exit(0 if ok else 1)


def parse_size(text):
    w, h = text.lower().split("x")
    return int(w), int(h)


def split_pair(text):
    if "=" not in text:
        die("expected NAME=VALUE, got %r" % text)
    return text.split("=", 1)


def cmd_doc(args):
    rep = Report()
    doc = info(args.file)
    if args.size:
        want = parse_size(args.size)
        rep.add("size %dx%d" % want, (doc["width"], doc["height"]) == want,
                "%dx%d" % (doc["width"], doc["height"]))
    if args.mode:
        rep.add("mode %s" % args.mode, str(doc.get("mode", "")).lower() == args.mode.lower(), doc.get("mode"))
    if args.depth:
        rep.add("depth %d" % args.depth, doc.get("depth") == args.depth, doc.get("depth"))
    for name in args.has:
        rep.add("has layer %r" % name, find_layer(doc, name) is not None)
    for name in args.visible:
        layer = find_layer(doc, name)
        rep.add("%r visible" % name, bool(layer and layer.get("visible")),
                "missing" if layer is None else "visible=%s" % layer.get("visible"))
    for name in args.hidden:
        layer = find_layer(doc, name)
        rep.add("%r hidden" % name, bool(layer and not layer.get("visible")),
                "missing" if layer is None else "visible=%s" % layer.get("visible"))
    for pair in args.text:
        name, text = split_pair(pair)
        layer = find_layer(doc, name)
        got = ((layer or {}).get("text") or {}).get("text")
        rep.add("%r text == %r" % (name, text), got == text, repr(got))
    for pair in args.effect:
        name, kind = split_pair(pair)
        layer = find_layer(doc, name)
        kinds = [e.get("kind") for e in ((layer or {}).get("effects") or {}).get("items") or []]
        rep.add("%r has effect %r" % (name, kind), kind in kinds, kinds)
    if args.order:
        names = [layer.get("name") for _, layer in walk(doc.get("layers") or [])]
        wanted = [n.strip() for n in args.order.split(",")]
        pos = [names.index(n) if n in names else -1 for n in wanted]
        rep.add("order %s" % " > ".join(wanted), -1 not in pos and pos == sorted(pos), names)
    rep.finish()


def webp_kind(path):
    with open(path, "rb") as handle:
        head = handle.read(64)
    if head[:4] != b"RIFF" or head[8:12] != b"WEBP":
        return "not-webp"
    chunk = head[12:16]
    if chunk == b"VP8 ":
        return "lossy"
    if chunk == b"VP8L":
        return "lossless"
    # VP8X: an extended file; look for the first image chunk.
    with open(path, "rb") as handle:
        data = handle.read(1 << 20)
    if b"VP8 " in data[12:]:
        return "lossy"
    if b"VP8L" in data[12:]:
        return "lossless"
    return "unknown"


def cmd_files(args):
    rep = Report()
    names = sorted(n for n in os.listdir(args.dir)
                   if os.path.splitext(n)[1].lower() in IMAGE_EXTS and not n.startswith("."))
    if args.count is not None:
        rep.add("count == %d" % args.count, len(names) == args.count, len(names))
    want_size = parse_size(args.size) if args.size else None
    for name in names:
        path = os.path.join(args.dir, name)
        if args.ext:
            rep.add("%s ext .%s" % (name, args.ext.lstrip(".")),
                    name.lower().endswith("." + args.ext.lstrip(".").lower()))
        if want_size or args.long_edge:
            try:
                doc = info(path)
            except PcError as exc:
                rep.add("%s readable" % name, False, str(exc))
                continue
            w, h = doc["width"], doc["height"]
            if want_size:
                rep.add("%s size %dx%d" % ((name,) + want_size), (w, h) == want_size, "%dx%d" % (w, h))
            if args.long_edge:
                rep.add("%s long edge %d" % (name, args.long_edge), max(w, h) == args.long_edge, "%dx%d" % (w, h))
        if args.webp:
            kind = webp_kind(path)
            rep.add("%s webp %s" % (name, args.webp), kind == args.webp, kind)
    rep.finish()


def manifest(directory):
    out = {}
    for root, _, files in os.walk(directory):
        for name in files:
            path = os.path.join(root, name)
            digest = hashlib.sha256()
            with open(path, "rb") as handle:
                for block in iter(lambda: handle.read(1 << 20), b""):
                    digest.update(block)
            out[os.path.relpath(path, directory)] = digest.hexdigest()
    return out


def cmd_hash(args):
    current = manifest(args.dir)
    if not args.compare:
        print(json.dumps(current, indent=2, sort_keys=True))
        return
    with open(args.compare) as handle:
        before = json.load(handle)
    rep = Report()
    changed = sorted(k for k in before if k in current and current[k] != before[k])
    missing = sorted(k for k in before if k not in current)
    added = sorted(k for k in current if k not in before)
    rep.add("no file changed", not changed, changed)
    rep.add("no file missing", not missing, missing)
    rep.add("no file added", not added, added)
    rep.finish()


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="action")
    p = sub.add_parser("doc")
    p.add_argument("file")
    p.add_argument("--size")
    p.add_argument("--mode")
    p.add_argument("--depth", type=int)
    for flag in ("--has", "--visible", "--hidden", "--text", "--effect"):
        p.add_argument(flag, action="append", default=[])
    p.add_argument("--order")
    p = sub.add_parser("files")
    p.add_argument("dir")
    p.add_argument("--count", type=int)
    p.add_argument("--ext")
    p.add_argument("--size")
    p.add_argument("--long-edge", type=int)
    p.add_argument("--webp", choices=["lossy", "lossless"])
    p = sub.add_parser("hash")
    p.add_argument("dir")
    p.add_argument("--compare")
    args = parser.parse_args()
    try:
        {"doc": cmd_doc, "files": cmd_files, "hash": cmd_hash}.get(
            args.action, lambda _: (parser.print_help(), sys.exit(2)))(args)
    except PcError as exc:
        die(str(exc))


if __name__ == "__main__":
    main()
