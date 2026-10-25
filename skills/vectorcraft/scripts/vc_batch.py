#!/usr/bin/env python3
"""Convert a folder of files with vectorcraft-cli convert, never writing into the input.

    vc_batch.py IN_DIR OUT_DIR --to svg[,pdf,png…] [--ext ai,eps,pdf] [--recursive]
                [--outline-text] [--decimals N] [--scale N] [--artboard I | --range R]
                [--each-artboard] [--overwrite] [--dry-run]

Each input becomes OUT_DIR/<relative stem>.<ext> per target format (with
--each-artboard: <stem>-<n>.<ext> for every artboard, for raster/SVG targets).
Inputs sharing a stem (logo.ai + logo.eps) become <stem>-<srcext>.<ext> instead.
Prints a JSON report with each file's result, its export warnings and the
importWarnings (what reading it left out); exits 1 if any file failed.
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vclib import cli, info  # noqa: E402

READABLE = {"vectorcraft", "drawcraft", "svg", "svgz", "pdf", "ai", "ait", "eps", "epsf", "ps", "dxf",
            "emf", "wmf", "psd", "psb", "af", "afdesign", "afpub", "vctemplate", "png", "jpg", "jpeg",
            "gif", "webp", "tif", "tiff", "bmp"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("indir")
    ap.add_argument("outdir")
    ap.add_argument("--to", required=True, help="comma-separated target extensions")
    ap.add_argument("--ext", help="only these input extensions (comma-separated)")
    ap.add_argument("--recursive", action="store_true")
    ap.add_argument("--outline-text", action="store_true")
    ap.add_argument("--decimals", type=int)
    ap.add_argument("--scale", type=float)
    ap.add_argument("--artboard", type=int)
    ap.add_argument("--range")
    ap.add_argument("--each-artboard", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    indir, outdir = os.path.realpath(a.indir), os.path.realpath(a.outdir)
    if outdir == indir or outdir.startswith(indir + os.sep):
        sys.exit("OUT_DIR must not be IN_DIR or inside it: originals stay untouched")
    exts = set(e.strip(".").lower() for e in a.ext.split(",")) if a.ext else READABLE
    targets = [t.strip(".").lower() for t in a.to.split(",")]

    files = []
    for dirpath, dirs, names in os.walk(indir):
        if not a.recursive:
            dirs[:] = []
        for n in sorted(names):
            if not n.startswith(".") and n.rsplit(".", 1)[-1].lower() in exts:
                files.append(os.path.join(dirpath, n))

    # Inputs sharing a stem (logo.ai, logo.eps) would write the same output: name those
    # <stem>-<srcext> instead of letting one silently replace the other.
    stems = {}
    for f in files:
        stems.setdefault(os.path.splitext(os.path.relpath(f, indir))[0].lower(), []).append(f)
    jobs = []
    for f in files:
        rel, src_ext = os.path.splitext(os.path.relpath(f, indir))
        if len(stems[rel.lower()]) > 1:
            rel = "%s-%s" % (rel, src_ext.strip(".").lower())
        count = len(info(f)["artboards"]) if a.each_artboard else 1
        for t in targets:
            if a.each_artboard and t not in ("pdf", "ai", "eps") and count > 1:
                for i in range(count):
                    jobs.append((f, os.path.join(outdir, "%s-%d.%s" % (rel, i + 1, t)), i))
            else:
                jobs.append((f, os.path.join(outdir, "%s.%s" % (rel, t)), a.artboard))
    if a.dry_run:
        print(json.dumps([{"in": j[0], "out": j[1], "artboard": j[2]} for j in jobs], indent=1))
        return 0
    clash = [j[1] for j in jobs if os.path.exists(j[1])]
    if clash and not a.overwrite:
        sys.exit("refusing to overwrite (pass --overwrite): " + ", ".join(clash[:10]))

    report, failed = [], 0
    for src, dst, artboard in jobs:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        args = [cli(), "convert", src, dst]
        if a.outline_text:
            args.append("--outline-text")
        if a.decimals is not None:
            args += ["--decimals", str(a.decimals)]
        if a.scale:
            args += ["--scale", str(a.scale)]
        if artboard is not None:
            args += ["--artboard", str(artboard)]
        elif a.range:
            args += ["--range", a.range]
        proc = subprocess.run(args, capture_output=True, text=True)
        entry = {"in": os.path.relpath(src, indir), "out": dst, "ok": proc.returncode == 0}
        try:
            res = json.loads(proc.stdout)
            entry["warnings"] = res.get("warnings", [])
            if res.get("importWarnings"):
                entry["importWarnings"] = res["importWarnings"]
        except ValueError:
            entry["error"] = (proc.stderr or proc.stdout).strip()[:500]
        if proc.returncode != 0:
            failed += 1
            entry.setdefault("error", (proc.stderr or proc.stdout).strip()[:500])
        report.append(entry)
    print(json.dumps({"converted": len(report) - failed, "failed": failed, "files": report}, indent=1))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
