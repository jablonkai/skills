#!/usr/bin/env python3
"""Logo or text watermark on images or whole folders, into a NEW folder, verified.

  python3 im_watermark.py photos/ --out marked/ --logo logo.png --gravity southeast --opacity 0.4
  python3 im_watermark.py photos/ --out marked/ --text "© 2026 Jane Doe" --opacity 0.6 --stroke black

The logo is scaled per image to --scale × the image's shorter side (so portrait and
landscape shots get the same visual size) and offset --margin × the shorter side from the
edge. Opacity multiplies the logo's own alpha, so its transparent areas stay transparent.
Verification: size unchanged, the mark box differs from the source, and everything
outside the box matches the source (RMSE below --tolerance).
"""
import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import imcommon as im  # noqa: E402

GRAVITIES = ["northwest", "north", "northeast", "west", "center", "east", "southwest", "south", "southeast"]


def box(gravity, W, H, w, h, mx, my):
    """Top-left of a w×h overlay placed with -gravity G -geometry +mx+my on a W×H image."""
    g = gravity.lower()
    x = mx if "west" in g else W - w - mx if "east" in g else (W - w) // 2 + mx
    y = my if "north" in g else H - h - my if "south" in g else (H - h) // 2 + my
    return x, y


def distortion(args):
    out = im.run(args + ["-metric", "RMSE", "-compare", "-format", "%[distortion]", "info:"], ok=(0, 1)).stdout
    return float(out.strip() or 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="image files and/or folders")
    ap.add_argument("--out", required=True, help="output folder (never an input folder)")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--logo", help="logo image, ideally PNG with transparency")
    src.add_argument("--text", help="text to stamp")
    ap.add_argument("--gravity", default="southeast", choices=GRAVITIES)
    ap.add_argument("--opacity", type=float, default=0.4, help="0-1, multiplies the logo alpha (default 0.4)")
    ap.add_argument("--scale", type=float, default=0.15, help="logo width or text height × shorter side (default 0.15 logo, 0.04 text)")
    ap.add_argument("--margin", type=float, default=0.03, help="edge offset × shorter side (default 0.03)")
    ap.add_argument("--font", help="font file for --text (default: Arial/Helvetica/DejaVu file)")
    ap.add_argument("--color", default="white", help="text colour (default white)")
    ap.add_argument("--stroke", help="text outline colour for legibility on mixed backgrounds")
    ap.add_argument("--format", help="output format (default: keep)")
    ap.add_argument("--quality", type=int, default=92, help="encoder quality (default 92)")
    ap.add_argument("--suffix", default="")
    ap.add_argument("--tolerance", type=float, default=0.02, help="max RMSE outside the mark box (default 0.02)")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    if not 0 < a.opacity <= 1:
        im.die("--opacity must be in (0, 1]")

    files, skipped = im.list_images(a.inputs)
    if a.logo:
        files = [f for f in files if os.path.realpath(f) != os.path.realpath(a.logo)]
        logo = im.identify(a.logo)
        if "error" in logo:
            im.die(f"cannot read logo {a.logo}: {logo['error']}")
    font = im.resolve_font(a.font) if a.text else None
    scale = a.scale if (a.logo or a.scale != 0.15) else 0.04
    ext = im.FORMAT_EXT.get(a.format.lower()) if a.format else None
    im.out_dir(a.out, files)
    originals = im.Originals(files + ([a.logo] if a.logo else []))

    def work(srcf):
        info = im.identify(srcf)
        if "error" in info:
            return {"src": srcf, "error": info["error"]}
        W, H = im.display_size(info)
        short = min(W, H)
        m = max(1, round(short * a.margin))
        if a.logo:
            lw = max(1, round(short * scale))
            lh = max(1, round(lw * logo["height"] / logo["width"]))
            overlay = ["(", a.logo, "-resize", f"{lw}x{lh}!"]
        else:
            pts = max(6, round(short * scale))
            overlay = ["(", "-background", "none", "-font", font, "-pointsize", str(pts), "-fill", a.color]
            if a.stroke:
                overlay += ["-stroke", a.stroke, "-strokewidth", str(max(1, pts // 25))]
            overlay += [f"label:{a.text}"]
            dims = im.run(overlay[1:] + ["-format", "%w %h", "info:"]).stdout.split()
            lw, lh = int(dims[0]), int(dims[1])
        overlay += ["-alpha", "set", "-channel", "A", "-evaluate", "multiply", str(a.opacity), "+channel", ")"]
        dst = im.out_name(srcf, a.out, ext, a.suffix)
        args = [srcf, "-auto-orient", *overlay, "-gravity", a.gravity, "-geometry", f"+{m}+{m}",
                "-compose", "over", "-composite", *im.quality_args(dst.rsplit(".", 1)[-1].lower(), a.quality), dst]
        im.run(args)

        o = im.identify(dst)
        x, y = box(a.gravity, W, H, lw, lh, m, m)
        pad = 2
        rect = f"rectangle {max(0, x - pad)},{max(0, y - pad)} {min(W, x + lw + pad)},{min(H, y + lh + pad)}"
        crop = f"{lw}x{lh}+{x}+{y}"
        outside = distortion([srcf, "-auto-orient", "-fill", "black", "-draw", rect,
                              dst, "-fill", "black", "-draw", rect])
        inside = distortion(["(", srcf, "-auto-orient", "-crop", crop, "+repage", ")",
                             "(", dst, "-crop", crop, "+repage", ")"])
        rec = {"src": srcf, "out": dst, "size": f"{o.get('width')}x{o.get('height')}",
               "mark_box": f"{lw}x{lh}+{x}+{y}", "rmse_outside": round(outside, 5), "rmse_inside": round(inside, 5)}
        problems = []
        if (o.get("width"), o.get("height")) != (W, H):
            problems.append(f"size changed to {o.get('width')}x{o.get('height')}")
        if outside > a.tolerance:
            problems.append(f"pixels outside the mark box changed (RMSE {outside:.4f})")
        if inside < 0.002:
            problems.append("mark box looks unchanged: watermark missing or invisible")
        if problems:
            rec["problems"] = problems
        return rec

    with ThreadPoolExecutor(max_workers=max(1, a.jobs)) as pool:
        results = list(pool.map(work, files))
    changed = originals.changed()
    bad = [r for r in results if "error" in r or "problems" in r]
    im.emit({"ok": not bad and not changed, "inputs": len(files), "out_dir": a.out,
             "font": font, "skipped_non_images": skipped, "originals_unchanged": not changed,
             "changed_originals": changed, "results": results})
    sys.exit(0 if not bad and not changed else 1)


if __name__ == "__main__":
    main()
