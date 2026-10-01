#!/usr/bin/env python3
"""Batch-process image files or folders through Pixelmator Pro, one document at a time.

usage: pxm-batch.py SRC... --out DIR [--format jpeg] [--quality 85]
                    [--ops remove-bg,super-res,enhance,denoise,auto-light,auto-color,
                           auto-white-balance,trim]
                    [--resize WxH|wN|hN|fitN] [--suffix TEXT] [--no-recursive]
                    [--overwrite] [--dry-run] [--timeout SECS] [--summary FILE.json]

Folders are walked recursively (subfolders are mirrored under --out). Ops run in the
order given, then the resize, then the export. Inputs are never modified. Existing
outputs are skipped unless --overwrite. Prints one JSON line per file; exit code is
0 when every file succeeded or was skipped, 1 if any failed, 2 on bad arguments.
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROCESS = os.path.join(HERE, "pxm-process.applescript")
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".tif", ".tiff", ".webp",
              ".gif", ".bmp", ".psd", ".pxd", ".avif", ".jp2"}
FORMATS = {"png": ".png", "jpeg": ".jpg", "jpg": ".jpg", "heic": ".heic", "webp": ".webp",
           "avif": ".avif", "tiff": ".tiff", "tif": ".tiff", "psd": ".psd", "pdf": ".pdf",
           "gif": ".gif", "pxd": ".pxd"}
NO_ALPHA = {"jpeg", "jpg"}
OPS = {"remove-bg", "super-res", "enhance", "denoise", "auto-light", "auto-color",
       "auto-white-balance", "trim"}


def collect(sources, recursive):
    """Yield (input path, path relative to its source root)."""
    for src in sources:
        src = os.path.abspath(src)
        if os.path.isfile(src):
            yield src, os.path.basename(src)
        elif os.path.isdir(src):
            for root, dirs, files in os.walk(src):
                dirs[:] = sorted(d for d in dirs if not d.startswith(".")) if recursive else []
                for f in sorted(files):
                    if os.path.splitext(f)[1].lower() in IMAGE_EXTS and not f.startswith("."):
                        p = os.path.join(root, f)
                        yield p, os.path.relpath(p, src)
        else:
            sys.exit("pxm-batch: no such file or folder: " + src)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sources", nargs="+")
    ap.add_argument("--out", required=True, help="output folder")
    ap.add_argument("--format", default="png", choices=sorted(FORMATS))
    ap.add_argument("--quality", type=int, default=0, help="1-100 for jpeg/heic/webp/avif")
    ap.add_argument("--ops", default="", help="comma list, run in order")
    ap.add_argument("--resize", default="", help="WxH, wN, hN or fitN (long edge)")
    ap.add_argument("--suffix", default="", help="added to each output basename")
    ap.add_argument("--no-recursive", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--timeout", type=int, default=600, help="per file, seconds")
    ap.add_argument("--summary", help="also write all results to this JSON file")
    a = ap.parse_args()

    ops = [o.strip() for o in a.ops.split(",") if o.strip()]
    bad = [o for o in ops if o not in OPS]
    if bad:
        ap.error("unknown op(s): %s (choose from %s)" % (", ".join(bad), ", ".join(sorted(OPS))))
    if not 0 <= a.quality <= 100:
        ap.error("--quality must be 1-100")
    if "remove-bg" in ops and a.format in NO_ALPHA:
        print("pxm-batch: warning: JPEG has no alpha; removed background will be flattened", file=sys.stderr)

    out_root = os.path.abspath(a.out)
    ext = FORMATS[a.format]
    jobs, seen = [], {}
    for src, rel in collect(a.sources, not a.no_recursive):
        stem = os.path.splitext(rel)[0]
        dst = os.path.join(out_root, stem + a.suffix + ext)
        if os.path.realpath(dst) == os.path.realpath(src):
            sys.exit("pxm-batch: output would overwrite its input: %s (use --out elsewhere or --suffix)" % src)
        if dst in seen:
            sys.exit("pxm-batch: %s and %s both map to %s" % (seen[dst], src, dst))
        seen[dst] = src
        jobs.append((src, dst))
    if not jobs:
        sys.exit("pxm-batch: no images found")

    results, failed = [], 0
    for src, dst in jobs:
        if os.path.exists(dst) and not a.overwrite:
            r = {"in": src, "out": dst, "status": "skipped (exists)"}
        elif a.dry_run:
            r = {"in": src, "out": dst, "status": "dry-run", "ops": ops, "resize": a.resize}
        else:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            t0 = time.time()
            p = subprocess.run(
                ["bash", os.path.join(HERE, "pxm.sh"), "run", PROCESS, "--timeout", str(a.timeout),
                 src, dst, a.format, str(a.quality), ",".join(ops), a.resize],
                capture_output=True, text=True)
            if p.returncode == 0 and os.path.isfile(dst):
                r = json.loads(p.stdout)
                r["status"] = "ok"
            else:
                failed += 1
                r = {"in": src, "out": dst, "status": "failed", "exit": p.returncode,
                     "error": p.stderr.strip().splitlines()[-1:] or [""]}
                r["error"] = r["error"][0]
                if p.returncode == 3:  # Automation permission: every other file would fail too
                    print(json.dumps(r, ensure_ascii=False))
                    sys.exit(3)
            r["seconds"] = round(time.time() - t0, 1)
        results.append(r)
        print(json.dumps(r, ensure_ascii=False), flush=True)

    if a.summary:
        with open(a.summary, "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    print("pxm-batch: %d file(s), %d failed" % (len(results), failed), file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
