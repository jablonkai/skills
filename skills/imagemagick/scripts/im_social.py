#!/usr/bin/env python3
"""Fixed-aspect versions of photos (square, story, OG…) without cutting the subject off.

  python3 im_social.py beach.jpg --out social/ --preset square --preset story
  python3 im_social.py photos/ --out social/ --size 1080x1350 --fill color --background "#111"
  python3 im_social.py beach.jpg --out social/ --size 1200x630 --fill crop

--fill blur  (default) the whole photo fitted in the frame, centred over a blurred,
             darkened, cover-scaled copy of itself
--fill color the photo fitted over a flat --background
--fill crop  cover the frame and cut the overflow (the subject may be cut)
Outputs are named STEM_WxH.EXT. Verification: exact size, and for blur/color the centre
band matches the photo fitted to the frame (nothing cropped).
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import imcommon as im  # noqa: E402

PRESETS = {"square": "1080x1080", "portrait": "1080x1350", "story": "1080x1920", "reel": "1080x1920",
           "landscape": "1080x566", "og": "1200x630", "x": "1600x900", "youtube": "1280x720"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="image files and/or folders")
    ap.add_argument("--out", required=True, help="output folder (never an input folder)")
    ap.add_argument("--size", action="append", default=[], metavar="WxH", help="target size; repeatable")
    ap.add_argument("--preset", action="append", default=[], choices=sorted(PRESETS),
                    help="named size: " + ", ".join(f"{k}={v}" for k, v in PRESETS.items()))
    ap.add_argument("--fill", choices=["blur", "color", "crop"], default="blur")
    ap.add_argument("--background", default="black", help="pad colour for --fill color")
    ap.add_argument("--blur", type=float, default=30, help="blur sigma at 1080 px, scaled with size (default 30)")
    ap.add_argument("--dim", type=float, default=0.75, help="background brightness for --fill blur (default 0.75)")
    ap.add_argument("--gravity", default="center", help="anchor for --fill crop (default center)")
    ap.add_argument("--format", help="output format (default: keep)")
    ap.add_argument("--quality", type=int, default=90)
    a = ap.parse_args()
    sizes = [im.parse_size(s) for s in a.size] + [im.parse_size(PRESETS[p]) for p in a.preset]
    if not sizes:
        im.die("give at least one --size WxH or --preset")

    files, skipped = im.list_images(a.inputs)
    ext = im.FORMAT_EXT.get(a.format.lower()) if a.format else None
    im.out_dir(a.out, files)
    originals = im.Originals(files)
    results, bad = [], False
    for src in files:
        info = im.identify(src)
        if "error" in info:
            results.append({"src": src, "error": info["error"]})
            bad = True
            continue
        base = [src, "-auto-orient"] + im.to_srgb_args(info)
        for W, H in sizes:
            dst = im.out_name(src, a.out, ext, f"_{W}x{H}")
            q = im.quality_args(dst.rsplit(".", 1)[-1].lower(), a.quality)
            fit = ["-resize", f"{W}x{H}"]
            if a.fill == "crop":
                args = base + ["-resize", f"{W}x{H}^", "-gravity", a.gravity, "-extent", f"{W}x{H}", "+repage"]
            elif a.fill == "color":
                args = base + fit + ["-background", a.background, "-gravity", "center", "-extent", f"{W}x{H}", "+repage"]
            else:
                sigma = a.blur * max(W, H) / 1080
                # blur a small copy then scale up: same look, a fraction of the cost of a big sigma
                args = base + ["-write", "mpr:src", "+delete",
                               "mpr:src", "-resize", f"{W // 4}x{H // 4}^", "-gravity", "center",
                               "-extent", f"{W // 4}x{H // 4}", "-blur", f"0x{sigma / 4:.1f}",
                               "-resize", f"{W}x{H}!", "-evaluate", "multiply", str(a.dim),
                               "(", "mpr:src", *fit, ")", "-gravity", "center", "-compose", "over", "-composite",
                               "+repage"]
            im.run(args + ["-strip"] + q + [dst])

            o = im.identify(dst)
            rec = {"src": src, "out": dst, "size": f"{o.get('width')}x{o.get('height')}", "fill": a.fill}
            problems = []
            if (o.get("width"), o.get("height")) != (W, H):
                problems.append(f"size {rec['size']}, expected {W}x{H}")
            elif a.fill != "crop":
                # the fitted photo must sit intact in the centre
                fw, fh = (int(v) for v in im.run(base + fit + ["-format", "%w %h", "info:"]).stdout.split())
                crop = f"{fw}x{fh}+{(W - fw) // 2}+{(H - fh) // 2}"
                d = im.run(["(", *base, *fit, ")", "(", dst, "-crop", crop, "+repage", ")",
                            "-metric", "RMSE", "-compare", "-format", "%[distortion]", "info:"], ok=(0, 1)).stdout
                rec["centre_rmse"] = round(float(d or 1), 5)
                if rec["centre_rmse"] > 0.03:
                    problems.append(f"centre does not match the fitted photo (RMSE {rec['centre_rmse']})")
            if problems:
                rec["problems"] = problems
                bad = True
            results.append(rec)
    changed = originals.changed()
    im.emit({"ok": not bad and not changed, "inputs": len(files), "sizes": [f"{w}x{h}" for w, h in sizes],
             "skipped_non_images": skipped, "originals_unchanged": not changed, "results": results})
    sys.exit(0 if not bad and not changed else 1)


if __name__ == "__main__":
    main()
