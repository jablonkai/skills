#!/usr/bin/env python3
"""Convert every DXF/DWG in a folder with `cadcraft-cli convert`.

    cc_batch.py IN_DIR OUT_DIR --to pdf,svg[,png,dxf,dwg] [--view extents | --window=x0,y0,x1,y1]
                [--recursive] [--overwrite]

- OUT_DIR must not be IN_DIR or lie inside it (the originals' folder is never written).
- Image outputs always get explicit framing (default --view extents).
- Two inputs with the same stem (plan.dxf + plan.dwg) are written as plan-dxf.* and
  plan-dwg.* instead of overwriting each other.
- Writes OUT_DIR/manifest.json: SHA-256 of every input before and after, and each output.
Prints a JSON summary; exits 1 if any conversion failed or an input changed.
"""
import argparse
import collections
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cclib import DRAWING_EXTS, convert, inside  # noqa: E402

FORMATS = ("pdf", "svg", "png", "dxf", "dwg")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_inputs(root, recursive):
    found = []
    for d, dirs, files in os.walk(root):
        dirs.sort()
        for name in sorted(files):
            if name.lower().endswith(DRAWING_EXTS) and not name.startswith("."):
                found.append(os.path.join(d, name))
        if not recursive:
            break
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("in_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--to", required=True, help="comma-separated: " + ",".join(FORMATS))
    ap.add_argument("--view", choices=["extents", "current"])
    ap.add_argument("--window")
    ap.add_argument("--recursive", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args()

    src, dst = os.path.abspath(a.in_dir), os.path.abspath(a.out_dir)
    if inside(dst, src):
        sys.exit("OUT_DIR %s is inside IN_DIR: pick a folder outside the originals" % dst)
    fmts = [f.strip().lower().lstrip(".") for f in a.to.split(",") if f.strip()]
    bad = [f for f in fmts if f not in FORMATS]
    if bad:
        sys.exit("unsupported --to %s (use %s)" % (bad, ",".join(FORMATS)))

    inputs = find_inputs(src, a.recursive)
    if not inputs:
        sys.exit("no .dxf/.dwg files in %s" % src)
    before = {p: sha256(p) for p in inputs}
    stems = collections.Counter(
        os.path.join(os.path.relpath(os.path.dirname(p), src), os.path.splitext(os.path.basename(p))[0])
        for p in inputs)

    results, failed = [], 0
    for p in inputs:
        rel_dir = os.path.relpath(os.path.dirname(p), src)
        stem, ext = os.path.splitext(os.path.basename(p))
        if stems[os.path.join(rel_dir, stem)] > 1:
            stem = "%s-%s" % (stem, ext.lstrip(".").lower())
        out_dir = os.path.normpath(os.path.join(dst, rel_dir))
        os.makedirs(out_dir, exist_ok=True)
        for fmt in fmts:
            out = os.path.join(out_dir, "%s.%s" % (stem, fmt))
            entry = {"input": p, "output": out}
            if os.path.exists(out) and not a.overwrite:
                entry["error"] = "exists (pass --overwrite)"
            else:
                try:
                    convert(p, out, view=a.view, window=a.window)
                    entry["bytes"] = os.path.getsize(out)
                except RuntimeError as e:
                    entry["error"] = str(e)
            failed += "error" in entry
            results.append(entry)

    after = {p: sha256(p) for p in inputs}
    changed = [p for p in inputs if before[p] != after[p]]
    manifest = {"inputs": [{"path": p, "sha256_before": before[p], "sha256_after": after[p]}
                           for p in inputs], "outputs": results}
    with open(os.path.join(dst, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    summary = {"inputs": len(inputs), "outputs_ok": len(results) - failed, "failed": failed,
               "inputs_changed": changed, "manifest": os.path.join(dst, "manifest.json"),
               "errors": [r for r in results if "error" in r]}
    print(json.dumps(summary, indent=1))
    return 1 if failed or changed else 0


if __name__ == "__main__":
    sys.exit(main())
