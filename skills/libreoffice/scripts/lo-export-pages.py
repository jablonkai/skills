#!/usr/bin/env python3
"""Export every page (or chosen pages) of a document as images.

  python3 lo-export-pages.py deck.pptx --out-dir slides                 # PNG per slide
  python3 lo-export-pages.py deck.odp --out-dir slides --width 1920 --pages 1,3-5
  python3 lo-export-pages.py drawing.odg --out-dir out --format svg
  python3 lo-export-pages.py report.docx --out-dir pages --dpi 150      # via PDF

Impress and Draw documents are rendered page by page by LibreOffice itself (png, jpg,
svg, webp, tif, gif, bmp). `soffice --convert-to png` would give only the first page.
Hidden slides are skipped unless --include-hidden. Writer and Calc documents have no
page objects to render, so they go through a PDF and poppler's pdftoppm (png/jpg).
Existing images are replaced only with --force. Files are named <prefix><page>.<fmt>,
zero-padded to the page count.
Standard library only (python3 3.9).
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lo_run import LOError, real, run_ops, sniff  # noqa: E402


def parse_pages(spec):
    pages = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            pages.extend(range(int(lo), int(hi) + 1))
        elif part:
            pages.append(int(part))
    return pages


def via_pdf(src, a, pages):
    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        raise LOError("Writer/Calc pages are rasterized from a PDF with pdftoppm — "
                      "install poppler, or convert to PDF with lo-convert.py")
    if a.format not in ("png", "jpg"):
        raise LOError("Writer/Calc pages export as png or jpg only")
    tmp = tempfile.mkdtemp(prefix="lo-pages-")
    try:
        pdf = os.path.join(tmp, "doc.pdf")
        r = run_ops("convert", {"jobs": [{"src": src, "dst": pdf}]})["results"][0]
        if not r["ok"]:
            raise LOError(r["error"])
        cmd = [pdftoppm, "-" + ("jpeg" if a.format == "jpg" else "png")]
        if a.width:
            cmd += ["-scale-to-x", str(a.width), "-scale-to-y", str(a.height or -1)]
        else:
            cmd += ["-r", str(a.dpi)]
        files = []
        for p in pages or [None]:
            c = cmd + (["-f", str(p), "-l", str(p)] if p else [])
            subprocess.run(c + [pdf, os.path.join(tmp, "p")], check=True)
        n = len(glob.glob(os.path.join(tmp, "p-*")))
        for f in sorted(glob.glob(os.path.join(tmp, "p-*"))):
            num = int(os.path.splitext(f)[0].rsplit("-", 1)[1])
            dst = os.path.join(real(a.out_dir), "%s%0*d.%s" % (a.prefix, len(str(n)), num,
                                                              a.format))
            if os.path.exists(dst) and not a.force:
                raise LOError("%s exists (use --force)" % dst)
            shutil.move(f, dst)
            files.append({"page": num, "file": dst})
        return {"kind": r.get("kind"), "files": files}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("source")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--format", default="png", help="png (default), jpg, svg, webp, tif ...")
    ap.add_argument("--width", type=int, help="pixel width (height follows the page ratio)")
    ap.add_argument("--height", type=int, help="pixel height")
    ap.add_argument("--dpi", type=int, default=150, help="Writer/Calc raster DPI (default 150)")
    ap.add_argument("--pages", help="e.g. 1,3-5 (default: all)")
    ap.add_argument("--prefix", default="page-", help="file name prefix (default page-)")
    ap.add_argument("--quality", type=int, help="JPEG quality 1-100")
    ap.add_argument("--include-hidden", action="store_true", help="also hidden slides")
    ap.add_argument("--force", action="store_true", help="replace existing images")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    a.format = a.format.lower().lstrip(".").replace("jpeg", "jpg")

    src = real(a.source)
    bad = sniff(src)
    if bad:
        raise LOError("%s: %s" % (src, bad))
    pages = parse_pages(a.pages) if a.pages else None
    os.makedirs(real(a.out_dir), exist_ok=True)
    info = run_ops("inspect", {"src": src})
    if info["kind"] in ("impress", "draw"):
        n = info["pages"]
        for p in pages or range(1, n + 1):
            dst = os.path.join(real(a.out_dir), "%s%0*d.%s" % (a.prefix, len(str(n)), p,
                                                              a.format))
            if os.path.exists(dst) and not a.force:
                raise LOError("%s exists (use --force)" % dst)
        args = {"src": src, "out_dir": real(a.out_dir), "format": a.format,
                "width": a.width, "height": a.height, "pages": pages, "prefix": a.prefix,
                "quality": a.quality, "include_hidden": a.include_hidden}
        out = run_ops("export_pages", {k: v for k, v in args.items() if v is not None})
    else:
        out = via_pdf(src, a, pages)
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        for f in out["files"]:
            print("page %d: %s%s" % (f["page"], f["file"],
                                     "  (%s)" % f["name"] if f.get("name") else ""))
        print("%d images from a %s document" % (len(out["files"]), out["kind"]))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except LOError as e:
        print("error: %s" % e, file=sys.stderr)
        sys.exit(1)
