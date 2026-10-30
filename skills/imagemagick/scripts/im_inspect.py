#!/usr/bin/env python3
"""Read-back report for images: format, size, colourspace, profiles, EXIF/GPS, quality.

  python3 im_inspect.py out/                 # table
  python3 im_inspect.py a.jpg b.webp --json  # full JSON

`display` is the size a viewer shows (EXIF orientation applied). A file with
`orientation` set still needs -auto-orient before resizing. `gps: yes` means location
data would leak on upload.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import imcommon as im  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="image files and/or folders")
    ap.add_argument("--recursive", action="store_true")
    ap.add_argument("--json", action="store_true", help="JSON instead of a table")
    a = ap.parse_args()
    files, skipped = im.list_images(a.inputs, a.recursive)
    rows = []
    for f in files:
        i = im.identify(f)
        if "error" not in i:
            w, h = im.display_size(i)
            i["display"] = f"{w}x{h}"
        rows.append(i)
    if a.json:
        im.emit({"ok": all("error" not in r for r in rows), "count": len(rows),
                 "skipped_non_images": skipped, "images": rows})
    else:
        hdr = ("file", "format", "display", "colorspace", "depth", "alpha", "q", "icc", "exif", "gps", "orient", "KB")
        out = [hdr]
        for r in rows:
            if "error" in r:
                out.append((os.path.basename(r["file"]), "ERROR", r["error"][:60]) + ("",) * 9)
                continue
            out.append((os.path.basename(r["file"]), r["format"], r["display"], r["colorspace"], str(r["depth"]),
                        "yes" if r["alpha"] else "-", str(r["quality"] or "-"), (r["icc"] or "-")[:24],
                        "yes" if r["exif"] else "-", "yes" if r["gps"] else "-", r["orientation"] or "-",
                        str(round(r["size_bytes"] / 1024))))
        widths = [max(len(row[c]) for row in out) for c in range(len(hdr))]
        for row in out:
            print("  ".join(v.ljust(widths[c]) for c, v in enumerate(row)).rstrip())
        if skipped:
            print(f"skipped (not images): {', '.join(os.path.basename(s) for s in skipped)}")
    sys.exit(0 if all("error" not in r for r in rows) else 1)


if __name__ == "__main__":
    main()
