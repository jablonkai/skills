#!/usr/bin/env python3
"""Resize and/or convert images or whole folders into a NEW folder, then verify every output.

  python3 im_batch.py photos/ --out web/ --max 1600 --format webp --quality 82
  python3 im_batch.py a.heic b.heic --out jpg/ --format jpeg --quality 85 --srgb --strip
  python3 im_batch.py shots/ --out thumbs/ --exact 400x400 --fit crop

Each image: auto-orient (EXIF) -> colour-managed sRGB (--srgb) -> resize -> strip -> encode.
`--max`/`--width`/`--height` never upscale unless --upscale. Originals are checksummed
before and after; the output folder may not be an input folder. Prints a JSON report and
exits 0 only when every output has the expected size, format and colourspace.
"""
import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import imcommon as im  # noqa: E402


def resize_args(a):
    keep = "" if a.upscale else ">"
    if a.max:
        return ["-resize", f"{a.max}x{a.max}{keep}"]
    if a.width:
        return ["-resize", f"{a.width}{keep}"]
    if a.height:
        return ["-resize", f"x{a.height}{keep}"]
    if a.exact:
        w, h = im.parse_size(a.exact)
        if a.fit == "crop":
            return ["-resize", f"{w}x{h}^", "-gravity", a.gravity, "-extent", f"{w}x{h}", "+repage"]
        if a.fit == "stretch":
            return ["-resize", f"{w}x{h}!"]
        return ["-resize", f"{w}x{h}", "-background", a.background, "-gravity", a.gravity,
                "-extent", f"{w}x{h}", "+repage"]
    return []


def expected_size(a, w, h):
    if a.exact:
        if a.fit in ("crop", "stretch", "pad"):
            return im.parse_size(a.exact)
    limit = None
    if a.max:
        limit = a.max / max(w, h)
    elif a.width:
        limit = a.width / w
    elif a.height:
        limit = a.height / h
    if limit is None or (limit >= 1 and not a.upscale):
        return w, h
    return round(w * limit), round(h * limit)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="image files and/or folders")
    ap.add_argument("--out", required=True, help="output folder (created; never an input folder)")
    size = ap.add_mutually_exclusive_group()
    size.add_argument("--max", type=int, metavar="PX", help="long edge at most PX (no upscaling)")
    size.add_argument("--width", type=int, metavar="PX", help="width at most PX")
    size.add_argument("--height", type=int, metavar="PX", help="height at most PX")
    size.add_argument("--exact", metavar="WxH", help="exact output size, see --fit")
    ap.add_argument("--fit", choices=["pad", "crop", "stretch"], default="pad",
                    help="with --exact: pad (letterbox, default), crop (fill and cut), stretch")
    ap.add_argument("--background", default="white", help="pad colour for --fit pad (default white; 'none' = transparent)")
    ap.add_argument("--gravity", default="center", help="anchor for pad/crop (default center)")
    ap.add_argument("--upscale", action="store_true", help="allow enlarging smaller images")
    ap.add_argument("--format", help="output format: jpeg, png, webp, avif, heic, tiff, gif, jxl (default: keep)")
    ap.add_argument("--quality", type=int, help="encoder quality 1-100 (JPEG/WebP/AVIF/HEIC scales differ)")
    ap.add_argument("--lossless", action="store_true", help="WebP lossless")
    ap.add_argument("--srgb", action="store_true", help="convert to sRGB through the embedded ICC profile")
    ap.add_argument("--strip", action="store_true", help="drop EXIF/GPS/XMP/comments and profiles (after --srgb)")
    ap.add_argument("--no-auto-orient", action="store_true", help="keep pixel orientation as stored")
    ap.add_argument("--suffix", default="", help="added to each output stem, e.g. _1600")
    ap.add_argument("--recursive", action="store_true", help="walk sub-folders, mirroring them in --out")
    ap.add_argument("--jobs", type=int, default=4, help="parallel magick processes (default 4)")
    ap.add_argument("--dry-run", action="store_true", help="print the magick commands, write nothing")
    a = ap.parse_args()

    files, skipped = im.list_images(a.inputs, a.recursive)
    root = a.inputs[0] if a.recursive and len(a.inputs) == 1 and os.path.isdir(a.inputs[0]) else None
    ext = im.FORMAT_EXT.get(a.format.lower()) if a.format else None
    if a.format and not ext:
        im.die(f"unsupported --format {a.format}")

    if not a.dry_run:
        im.out_dir(a.out, files)  # refuse an input folder before anything is created
    jobs, seen, renamed = [], {}, []
    for src in files:
        dst = im.out_name(src, a.out, ext, a.suffix, root, create=not a.dry_run)
        if dst in seen:
            # IMG_0001.HEIC and IMG_0001.PNG would both become IMG_0001.jpg: keep both
            first = seen[dst]
            src_ext = os.path.splitext(src)[1].lstrip(".").lower()
            dst = im.out_name(src, a.out, ext, f"{a.suffix}_{src_ext}", root, create=not a.dry_run)
            if dst in seen:
                im.die(f"cannot find a free output name for {src}")
            renamed.append({"src": src, "out": dst, "clashed_with": first})
        seen[dst] = src
        jobs.append((src, dst))
    originals = im.Originals(files)
    out_ext = lambda d: d.rsplit(".", 1)[-1].lower()

    def work(job):
        src, dst = job
        info = im.identify(src)
        if "error" in info:
            return {"src": src, "error": info["error"]}
        args = [src]
        if not a.no_auto_orient:
            args.append("-auto-orient")
        if a.srgb:
            args += im.to_srgb_args(info)
        args += resize_args(a)
        if a.strip:
            args.append("-strip")
        args += im.quality_args(out_ext(dst), a.quality, a.lossless)
        args.append(dst)
        if a.dry_run:
            return {"src": src, "cmd": "magick " + " ".join(f"'{x}'" if any(c in x for c in " >^!") else x for x in map(str, args))}
        im.run(args)
        w, h = im.display_size(info) if not a.no_auto_orient else (info["width"], info["height"])
        ew, eh = expected_size(a, w, h)
        o = im.identify(dst)
        rec = {"src": src, "out": dst, "in": f"{w}x{h}", "out_size": f"{o.get('width')}x{o.get('height')}",
               "format": o.get("format"), "colorspace": o.get("colorspace"), "bytes": o.get("size_bytes")}
        problems = []
        if "error" in o:
            problems.append(f"unreadable output: {o['error']}")
        else:
            if abs(o["width"] - ew) > 1 or abs(o["height"] - eh) > 1:
                problems.append(f"size {o['width']}x{o['height']}, expected {ew}x{eh}")
            if a.srgb and o["colorspace"] not in ("sRGB", "Gray"):
                problems.append(f"colorspace {o['colorspace']}, expected sRGB")
            if a.strip and (o["exif"] or o["gps"]):
                problems.append("EXIF still present after --strip")
        if problems:
            rec["problems"] = problems
        return rec

    with ThreadPoolExecutor(max_workers=max(1, a.jobs)) as pool:
        results = list(pool.map(work, jobs))
    if a.dry_run:
        im.emit({"dry_run": True, "commands": [r.get("cmd") or r for r in results]})
        return
    changed = originals.changed()
    bad = [r for r in results if "error" in r or "problems" in r]
    im.emit({
        "ok": not bad and not changed, "inputs": len(files), "outputs": len(results) - len([r for r in results if "error" in r]),
        "out_dir": a.out, "skipped_non_images": skipped, "renamed_to_avoid_overwrite": renamed, "originals_unchanged": not changed,
        "changed_originals": changed, "results": results,
    })
    sys.exit(0 if not bad and not changed else 1)


if __name__ == "__main__":
    main()
