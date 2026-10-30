#!/usr/bin/env python3
"""Text, embedded images and page renders with poppler, each result checked.

  pdf_extract.py text   IN [OUT.txt|-] [--pages RANGE] [--mode layout|raw|plain|bbox]
  pdf_extract.py images IN OUTDIR [--pages RANGE] [--prefix img] [--drop-smasks]
  pdf_extract.py render IN OUTDIR [--pages RANGE] [--dpi 150] [--format png|jpeg|tiff|svg|pdf] [--prefix page]

text:   pages are separated by form feeds; --mode bbox writes pdftotext's word-box XHTML.
images: pdfimages -all keeps the native encoding (JPEG stays a byte-identical .jpg,
        JPEG 2000 .jp2, JBIG2 .jb2e, CCITT .ccitt); other images become .png. Soft masks
        (alpha channels) are written as separate gray PNGs and flagged as "smask".
render: one file per page named PREFIX-<page>.<ext> (no zero padding); raster sizes
        are checked against page size x DPI.
Encrypted inputs: --password-file/--password-env (decrypted to a private temp copy).
"""
import argparse
import glob
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdfcommon import (add_password_args, die, emit, page_count, page_sizes, parse_range,  # noqa: E402
                       pixels, read_password, readable, run, text_pages)


def image_size(path):
    """(w, h) for PNG/JPEG/TIFF-less files; None when the format isn't parsed here."""
    with open(path, "rb") as fh:
        head = fh.read(32)
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", head[16:24])
        if head[:2] == b"\xff\xd8":
            fh.seek(2)
            while True:
                marker = fh.read(2)
                if len(marker) < 2 or marker[0] != 0xFF:
                    return None
                if marker[1] in (0xD8, 0x01) or 0xD0 <= marker[1] <= 0xD7:
                    continue
                seg = struct.unpack(">H", fh.read(2))[0]
                if 0xC0 <= marker[1] <= 0xCF and marker[1] not in (0xC4, 0xC8, 0xCC):
                    h, w = struct.unpack(">xHH", fh.read(5))
                    return w, h
                fh.seek(seg - 2, 1)
    return None


def list_images(path, first, last):
    out = run(["pdfimages", "-list", "-f", str(first), "-l", str(last), path]).stdout.splitlines()
    rows = []
    for line in out[2:]:
        f = line.split()
        if len(f) >= 9:
            rows.append({"page": int(f[0]), "num": int(f[1]), "type": f[2], "width": int(f[3]),
                         "height": int(f[4]), "color": f[5], "enc": f[8]})
    return rows


def contiguous_runs(pages):
    runs, start = [], None
    for i, p in enumerate(pages):
        if start is None:
            start = p
        if i + 1 == len(pages) or pages[i + 1] != p + 1:
            runs.append((start, p))
            start = None
    return runs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("text")
    t.add_argument("inp")
    t.add_argument("out", nargs="?", default="-")
    t.add_argument("--mode", choices=["layout", "raw", "plain", "bbox"], default="layout")
    i = sub.add_parser("images")
    i.add_argument("inp")
    i.add_argument("outdir")
    i.add_argument("--prefix", default="img")
    i.add_argument("--drop-smasks", action="store_true", help="delete the separate alpha-mask PNGs")
    r = sub.add_parser("render")
    r.add_argument("inp")
    r.add_argument("outdir")
    r.add_argument("--dpi", type=float, default=150)
    r.add_argument("--format", choices=["png", "jpeg", "tiff", "svg", "pdf"], default="png")
    r.add_argument("--prefix", default="page")
    for p in sub.choices.values():
        p.add_argument("--pages", help="qpdf range syntax, default all")
        add_password_args(p)
    a = ap.parse_args()
    if not os.path.exists(a.inp):
        die(f"no such file: {a.inp}")
    pw = read_password(a.password_file, a.password_env)

    with readable(a.inp, pw) as src:
        n = page_count(src)
        pages = parse_range(a.pages, n) if a.pages else list(range(1, n + 1))

        if a.cmd == "text":
            if a.mode == "bbox":
                if a.out == "-":
                    die("bbox mode writes XHTML; give an output file")
                runs = contiguous_runs(sorted(set(pages)))
                if len(runs) > 1:
                    die("bbox mode needs one contiguous page range")
                run(["pdftotext", "-bbox-layout", "-f", str(runs[0][0]), "-l", str(runs[0][1]), src, a.out])
                words = len(re.findall(r"<word ", open(a.out, encoding="utf-8", errors="replace").read()))
                emit({"output": a.out, "pages": pages, "words": words, "ok": words > 0})
                sys.exit(0 if words else 1)
            texts = text_pages(src, pages, a.mode)
            body = "\f".join(t.rstrip("\f") for t in texts)
            empty = [p for p, t in zip(pages, texts) if not t.strip()]
            if a.out == "-":
                sys.stdout.write(body)
                if empty:
                    print(f"\nwarning: no text on pages {empty} (scanned? needs OCR)", file=sys.stderr)
                sys.exit(0)
            with open(a.out, "w", encoding="utf-8") as fh:
                fh.write(body)
            emit({"output": a.out, "pages": pages, "chars": len(body), "pages_without_text": empty,
                  "ok": len(empty) < len(pages)})
            sys.exit(0 if len(empty) < len(pages) else 1)

        os.makedirs(a.outdir, exist_ok=True)
        if a.cmd == "images":
            rows = []
            for first, last in contiguous_runs(sorted(set(pages))):
                rows += list_images(src, first, last)
                run(["pdfimages", "-all", "-p", "-f", str(first), "-l", str(last), src,
                     os.path.join(a.outdir, a.prefix)])
            files = []
            for row in rows:
                hits = glob.glob(os.path.join(a.outdir, f"{a.prefix}-{row['page']:03d}-{row['num']:03d}.*"))
                entry = dict(row, file=hits[0] if hits else None)
                if hits:
                    size = image_size(hits[0])
                    entry["size_ok"] = None if size is None else size == (row["width"], row["height"])
                if row["type"] in ("smask", "stencil") and a.drop_smasks and hits:
                    os.remove(hits[0])
                    entry["file"] = None
                    entry["dropped"] = True
                files.append(entry)
            real = [f for f in files if f["type"] == "image"]
            ok = all(f["file"] for f in real) and all(f.get("size_ok") is not False for f in files)
            emit({"outdir": a.outdir, "images": len(real),
                  "smasks": sum(f["type"] in ("smask", "stencil") for f in files),
                  "files": files, "ok": ok})
            sys.exit(0 if ok else 1)

        # render
        sizes = page_sizes(src)
        ext = {"jpeg": "jpg", "tiff": "tif"}.get(a.format, a.format)
        outs = []
        for p in pages:
            base = os.path.join(a.outdir, f"{a.prefix}-{p}")
            if a.format in ("svg", "pdf"):
                run(["pdftocairo", f"-{a.format}", "-f", str(p), "-l", str(p), src, f"{base}.{ext}"])
                outs.append({"page": p, "file": f"{base}.{ext}", "ok": os.path.exists(f"{base}.{ext}")})
                continue
            run(["pdftoppm", f"-{a.format}", "-r", str(a.dpi), "-f", str(p), "-l", str(p), "-singlefile", src, base])
            w, h, rot = sizes[p - 1]
            if rot in (90, 270):
                w, h = h, w
            want = (pixels(w, a.dpi), pixels(h, a.dpi))
            got = image_size(f"{base}.{ext}") if a.format != "tiff" else None
            ok = os.path.exists(f"{base}.{ext}") and (got is None or (abs(got[0] - want[0]) <= 2 and abs(got[1] - want[1]) <= 2))
            outs.append({"page": p, "file": f"{base}.{ext}", "pixels": got, "expected_pixels": want, "ok": ok})
        emit({"outdir": a.outdir, "dpi": a.dpi, "format": a.format, "files": outs, "ok": all(o["ok"] for o in outs)})
        sys.exit(0 if all(o["ok"] for o in outs) else 1)


if __name__ == "__main__":
    main()
