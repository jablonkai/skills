#!/usr/bin/env python3
"""Verify LightCraft results: original hashes, export folders, synced develop settings.

Usage:
  lc_verify.py hash DIR [--compare MANIFEST]   sha256 manifest of DIR (recursive) to stdout,
                                               or compare DIR against a saved manifest
  lc_verify.py files DIR [--count N] [--ext jpg] [--long-edge N | --max-long-edge N]
                         [--format jpeg]       check an export folder (dimensions via sips)
  lc_verify.py same (--library DIR | --demo) --ids 1,2,3|all [--ignore crop,masks,...]
                                               develop settings identical across photos

Every subcommand prints JSON and exits 1 when a check fails. `same` ignores what
develop.copy leaves out by default (crop, masks, spots, red_eye, orientation, version)
unless --ignore says otherwise.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys

import lclib

DEFAULT_IGNORE = "crop,masks,spots,red_eye,orientation,version"
SKIP_NAMES = {".DS_Store"}


def walk(root):
    for base, dirs, names in os.walk(root):
        dirs.sort()
        for name in sorted(names):
            if name not in SKIP_NAMES:
                yield os.path.relpath(os.path.join(base, name), root)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd_hash(args):
    root = os.path.abspath(os.path.expanduser(args.dir))
    if not os.path.isdir(root):
        lclib.die(f"not a directory: {root}")
    current = {rel: sha256(os.path.join(root, rel)) for rel in walk(root)}
    if not args.compare:
        print(json.dumps(current, indent=1))
        return 0
    with open(args.compare, encoding="utf-8") as fh:
        saved = json.load(fh)
    report = {
        "dir": root,
        "unchanged": sum(1 for k in saved if current.get(k) == saved[k]),
        "changed": sorted(k for k in saved if k in current and current[k] != saved[k]),
        "missing": sorted(k for k in saved if k not in current),
        "added": sorted(k for k in current if k not in saved),
    }
    report["ok"] = not (report["changed"] or report["missing"] or report["added"])
    print(json.dumps(report, indent=1))
    return 0 if report["ok"] else 1


def image_info(path):
    proc = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", "-g", "format", path],
                          capture_output=True, text=True)
    info = {}
    for line in proc.stdout.splitlines():
        if ":" in line and line.startswith("  "):
            key, value = (s.strip() for s in line.split(":", 1))
            info[key] = int(value) if value.isdigit() else value
    return info


def cmd_files(args):
    root = os.path.abspath(os.path.expanduser(args.dir))
    if not os.path.isdir(root):
        lclib.die(f"not a directory: {root}")
    files = list(walk(root))
    problems, rows = [], []
    if args.count is not None and len(files) != args.count:
        problems.append(f"expected {args.count} files, found {len(files)}")
    for rel in files:
        ext = os.path.splitext(rel)[1].lstrip(".").lower()
        info = image_info(os.path.join(root, rel))
        w, h = info.get("pixelWidth"), info.get("pixelHeight")
        long_edge = max(w, h) if isinstance(w, int) and isinstance(h, int) else None
        rows.append({"file": rel, "width": w, "height": h, "format": info.get("format")})
        if args.ext and ext != args.ext.lower().lstrip("."):
            problems.append(f"{rel}: extension .{ext}, expected .{args.ext}")
        if args.format and str(info.get("format", "")).lower() != args.format.lower():
            problems.append(f"{rel}: format {info.get('format')}, expected {args.format}")
        if long_edge is None and (args.long_edge or args.max_long_edge):
            problems.append(f"{rel}: could not read dimensions")
        elif args.long_edge and long_edge != args.long_edge:
            problems.append(f"{rel}: long edge {long_edge}, expected {args.long_edge}")
        elif args.max_long_edge and long_edge > args.max_long_edge:
            problems.append(f"{rel}: long edge {long_edge} > {args.max_long_edge}")
    report = {"dir": root, "count": len(files), "files": rows, "problems": problems,
              "ok": not problems}
    print(json.dumps(report, indent=1))
    return 0 if report["ok"] else 1


def cmd_same(args):
    session = lclib.session_args(args.library, args.demo)
    ids = lclib.parse_ids(args.ids, session)
    if len(ids) < 2:
        lclib.die("--ids needs at least two photos")
    ignore = [p for p in args.ignore.split(",") if p]
    settings = lclib.develop_of(session, ids)

    def kept(key):
        return not any(key == p or key.startswith(p + ".") for p in ignore)

    ref = ids[0]
    keys = sorted(k for k in set().union(*(s.keys() for s in settings.values())) if kept(k))
    differ = {}
    for k in keys:
        values = {i: settings[i].get(k) for i in ids}
        if len({json.dumps(v) for v in values.values()}) > 1:
            differ[k] = {str(i): v for i, v in values.items()}
    report = {"ids": ids, "reference": ref, "compared": len(keys), "ignored": ignore,
              "differ": differ, "ok": not differ}
    print(json.dumps(report, indent=1))
    return 0 if report["ok"] else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    h = sub.add_parser("hash")
    h.add_argument("dir")
    h.add_argument("--compare")
    f = sub.add_parser("files")
    f.add_argument("dir")
    f.add_argument("--count", type=int)
    f.add_argument("--ext")
    f.add_argument("--format")
    f.add_argument("--long-edge", type=int)
    f.add_argument("--max-long-edge", type=int)
    s = sub.add_parser("same")
    s.add_argument("--library")
    s.add_argument("--demo", action="store_true")
    s.add_argument("--ids", required=True)
    s.add_argument("--ignore", default=DEFAULT_IGNORE)
    args = ap.parse_args()
    return {"hash": cmd_hash, "files": cmd_files, "same": cmd_same}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
