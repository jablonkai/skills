#!/usr/bin/env python3
"""Compare two images: metrics, an exact count of differing pixels, and a diff image.

  python3 im_compare.py before.png after.png --diff diff.png
  python3 im_compare.py ref.jpg out.jpg --metric RMSE --threshold 0.01

`differing_pixels` counts pixels where ANY channel differs by more than --fuzz. Don't
use `compare -metric AE` for this: ImageMagick 7.1.2 averages AE over the channels, so a
pixel that changed in two of three channels counts as 0.67. Other 7.1.2 quirks handled
here: `-metric SSIM` returns a distortion (0 = identical, same as DSSIM), and PSNR is
reported in dB with 120 meaning identical. Exit 0 when the chosen metric passes
--threshold (default: no differing pixels). Images of different sizes are reported, not
compared, unless --resize-b is given.
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import imcommon as im  # noqa: E402


def compare(a, b, name):
    """`magick compare -metric NAME` -> (raw, normalised). It prints 'raw (normalised)' on stderr."""
    proc = subprocess.run([im.magick_path(), "compare", "-metric", name, a, b, "null:"],
                          capture_output=True, text=True, errors="replace")
    if proc.returncode not in (0, 1):
        im.die(f"compare -metric {name} failed: {proc.stderr.strip()[:300]}")
    m = re.match(r"\s*([-\d.eE+inf]+)\s*(?:\(([-\d.eE+]+)\))?", proc.stderr)
    if not m:
        return None, None
    raw = float(m.group(1))
    return raw, float(m.group(2)) if m.group(2) else raw


def mask_args(A, B, fuzz):
    """Pixels where any channel differs by more than fuzz% -> white, else black."""
    return [A, B, "-alpha", "off", "-compose", "difference", "-composite",
            "-threshold", f"{fuzz}%", "-separate", "-evaluate-sequence", "max"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--diff", help="write a diff image: changed pixels red over a faded copy of A")
    ap.add_argument("--fuzz", default="0%", help="per-channel tolerance, e.g. 3%% for JPEG noise (default 0%%)")
    ap.add_argument("--metric", default="PIXELS", choices=["PIXELS", "RMSE", "MAE", "PSNR", "SSIM"],
                    help="what --threshold tests (default PIXELS = fraction of differing pixels)")
    ap.add_argument("--threshold", type=float, default=0.0,
                    help="PIXELS/RMSE/MAE pass when <= threshold (normalised 0-1); "
                         "PSNR (dB) and SSIM (0-1) pass when >= threshold. Default 0")
    ap.add_argument("--resize-b", action="store_true", help="scale B to A's size before comparing")
    a = ap.parse_args()

    ia, ib = im.identify(a.a), im.identify(a.b)
    for i in (ia, ib):
        if "error" in i:
            im.die(f"cannot read {i['file']}: {i['error']}")
    keys = ("file", "format", "width", "height", "colorspace")
    rep = {"a": {k: ia[k] for k in keys}, "b": {k: ib[k] for k in keys}}
    A, B = f"{a.a}[0]", f"{a.b}[0]"
    W, H = ia["width"], ia["height"]
    tmp = None
    if (W, H) != (ib["width"], ib["height"]):
        if not a.resize_b:
            rep.update(ok=False, error="sizes differ; pass --resize-b to compare B scaled to A")
            im.emit(rep)
            sys.exit(1)
        fd, tmp = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        im.run([B, "-resize", f"{W}x{H}!", tmp])
        B = tmp
    try:
        ok = report(a, rep, A, B, W, H)
    finally:
        if tmp:
            os.remove(tmp)
    sys.exit(0 if ok else 1)


def report(a, rep, A, B, W, H):
    fuzz = a.fuzz.rstrip("%")
    count = round(float(im.run(mask_args(A, B, fuzz) + ["-format", "%[fx:mean*w*h]", "info:"]).stdout))
    rep.update(differing_pixels=count, differing_fraction=round(count / (W * H), 6), fuzz=a.fuzz)
    if count:
        rep["changed_bbox"] = im.run(mask_args(A, B, fuzz) + ["-format", "%@", "info:"]).stdout.strip()

    rmse = compare(A, B, "RMSE")[1]
    mae = compare(A, B, "MAE")[1]
    psnr_db = compare(A, B, "PSNR")[0]
    dssim = compare(A, B, "DSSIM")[1]
    rep.update(rmse=rmse, mae=mae, psnr_db=psnr_db, ssim=None if dssim is None else round(1 - dssim, 6), dssim=dssim)

    if a.diff:
        im.run(mask_args(A, B, fuzz) + ["-write", "mpr:mask", "+delete",
                                        A, "-alpha", "off", "-fill", "white", "-colorize", "70%",
                                        "(", "-size", f"{W}x{H}", "xc:red", ")", "mpr:mask",
                                        "-compose", "over", "-composite", a.diff])
        rep["diff"] = a.diff

    value = {"PIXELS": rep["differing_fraction"], "RMSE": rmse, "MAE": mae,
             "PSNR": psnr_db, "SSIM": rep["ssim"]}[a.metric]
    if value is None:
        ok = False
    elif a.metric in ("PSNR", "SSIM"):
        ok = value >= a.threshold
    else:
        ok = value <= a.threshold
    rep.update(metric=a.metric, value=value, threshold=a.threshold, ok=ok)
    im.emit(rep)
    return ok


if __name__ == "__main__":
    main()
