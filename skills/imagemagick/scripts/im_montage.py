#!/usr/bin/env python3
"""Labelled contact sheet (montage) from image files or a folder, verified.

  python3 im_montage.py photos/ sheet.jpg --cols 4
  python3 im_montage.py *.png sheet.png --cols 6 --tile 200x200 --label '%t' --title "Shoot 2026-10"

Tiles are in file-name order, row by row. Each image is fitted inside --tile (aspect
kept, centred). Labels default to the file name (`%f`); `%t` drops the extension, `none`
disables them. The font is passed as a file because ImageMagick builds without
fontconfig cannot resolve names. Verification: the sheet's width equals cols × (tile + 2 ×
spacing) and its height leaves room for every row and its label strip.
"""
import argparse
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import imcommon as im  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="image files and/or folders, then the output file last")
    ap.add_argument("--cols", type=int, default=4, help="columns (default 4)")
    ap.add_argument("--tile", default="300x300", help="max tile size WxH (default 300x300)")
    ap.add_argument("--spacing", type=int, default=8, help="gap around each tile in px (default 8)")
    ap.add_argument("--background", default="white")
    ap.add_argument("--label", default="%f", help="label template: %%f file name, %%t name without extension, "
                                                   "%%wx%%h size, or 'none' (default %%f)")
    ap.add_argument("--font", help="font file (default: Arial/Helvetica/DejaVu file)")
    ap.add_argument("--pointsize", type=int, default=14)
    ap.add_argument("--label-color", default="black")
    ap.add_argument("--title", help="optional title above the sheet")
    ap.add_argument("--quality", type=int, default=90)
    a = ap.parse_args()
    if len(a.inputs) < 2:
        im.die("give the inputs and then the output file")
    *inputs, out = a.inputs
    files, skipped = im.list_images(inputs)
    if os.path.realpath(out) in {os.path.realpath(f) for f in files}:
        im.die("output would overwrite an input")
    tw, th = im.parse_size(a.tile)
    labels = a.label.lower() != "none"
    font = im.resolve_font(a.font) if labels or a.title else None
    originals = im.Originals(files)

    args = ["montage", "-define", f"jpeg:size={tw * 2}x{th * 2}"]  # faster JPEG decode for big photos
    if font:
        args += ["-font", font, "-pointsize", str(a.pointsize), "-fill", a.label_color]
    args += ["-label", a.label if labels else ""]  # a setting: must come BEFORE the files it labels
    args += files
    args += ["-tile", f"{a.cols}x", "-geometry", f"{tw}x{th}+{a.spacing}+{a.spacing}", "-background", a.background]
    if a.title:
        args += ["-title", a.title]
    args += im.quality_args(out.rsplit(".", 1)[-1].lower(), a.quality) + [out]
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    im.run(args)

    o = im.identify(out)
    n = len(files)
    cols = min(a.cols, n)
    rows = math.ceil(n / a.cols)
    cell_w, cell_h = tw + 2 * a.spacing, th + 2 * a.spacing
    problems = []
    if "error" in o:
        problems.append(f"unreadable output: {o['error']}")
    else:
        if o["width"] != cols * cell_w:
            problems.append(f"width {o['width']}, expected {cols} × {cell_w} = {cols * cell_w}")
        min_h = rows * (cell_h + (a.pointsize if labels else 0))
        if o["height"] < min_h:
            problems.append(f"height {o['height']} < {min_h}: rows or label strips missing")
        label_strip = (o["height"] - (a.pointsize * 2 if a.title else 0)) / rows - cell_h
        if labels and label_strip < a.pointsize * 0.6:
            problems.append("no room for labels under the tiles; was -label given before the files?")
    changed = originals.changed()
    rep = {"ok": not problems and not changed, "out": out, "images": n, "grid": f"{cols}x{rows}",
           "tile": a.tile, "size": f"{o.get('width')}x{o.get('height')}", "font": font,
           "order": [os.path.basename(f) for f in files], "skipped_non_images": skipped,
           "originals_unchanged": not changed}
    if problems:
        rep["problems"] = problems
    im.emit(rep)
    sys.exit(0 if rep["ok"] else 1)


if __name__ == "__main__":
    main()
