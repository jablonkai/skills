#!/usr/bin/env python3
"""Export the screens (top-level frames) of a FigCraft file — without the main components,
loose layers or other clutter that `figcraft-cli export -o DIR` and multi-page PDFs pick up.

    fc_export.py FILE OUTDIR [--format png|jpg|webp|svg|pdf] [--scale N]
    fc_export.py FILE OUT.pdf --one-pdf           every screen as one page of a single PDF
      [--page NAME] [--frames Cart Payment …] [--include-components]
      [--bleed 3mm] [--crop-marks] [--bleed-marks] [--cmyk] [--suffix @2x] [--overwrite]

Per-file mode writes OUTDIR/<frame name><suffix>.<format>; repeated names get " 2", " 3".
--one-pdf moves everything that isn't a chosen screen to a scratch page inside the
session, then writes one page per screen in reading order (left to right, top to
bottom). FILE itself is never saved or changed. Prints the written files as JSON.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fclib import Session, refuse_existing  # noqa: E402

SCREEN_TYPES = ("FRAME", "SECTION")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("out")
    ap.add_argument("--format", default="png", choices=["png", "jpg", "webp", "svg", "pdf"])
    ap.add_argument("--scale", type=float, default=1)
    ap.add_argument("--suffix", default="", help='appended to each file name, e.g. "@2x"')
    ap.add_argument("--page", help="page name (default: the page the file opens on)")
    ap.add_argument("--frames", nargs="+", help="only these top-level frames (by name)")
    ap.add_argument("--include-components", action="store_true", help="also export main components")
    ap.add_argument("--one-pdf", action="store_true")
    ap.add_argument("--bleed")
    ap.add_argument("--crop-marks", action="store_true")
    ap.add_argument("--bleed-marks", action="store_true")
    ap.add_argument("--cmyk", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args()

    src = os.path.abspath(a.file)
    out = os.path.abspath(a.out)
    out_dir = os.path.dirname(out) if a.one_pdf else out
    os.makedirs(out_dir, exist_ok=True)
    print_opts = {k: v for k, v in (("bleed", a.bleed), ("cropMarks", a.crop_marks),
                                    ("bleedMarks", a.bleed_marks), ("cmyk", a.cmyk)) if v}

    s = Session(os.path.dirname(src), out_dir)
    try:
        s.tool("open_file", {"path": src})
        pages = s.cmd("page.list")
        if a.page:
            hit = [p for p in pages if p["name"] == a.page]
            if not hit:
                sys.exit("no page %r (pages: %s)" % (a.page, [p["name"] for p in pages]))
            page = hit[0]
            s.cmd("page.select", {"id": page["id"]})
        else:
            page = [p for p in pages if p.get("current")][0]
        top = [n for n in s.tree(depth=1) if n["parent"] is None and n["page"] == page["name"]]
        wanted = SCREEN_TYPES + (("COMPONENT", "COMPONENT_SET") if a.include_components else ())
        screens = [n for n in top if n["type"] in wanted]
        if a.frames:
            by_name = {}
            for n in screens:
                by_name.setdefault(n["name"], n)
            missing = [f for f in a.frames if f not in by_name]
            if missing:
                sys.exit("no top-level frame %s on page %r (have: %s)" % (
                    missing, page["name"], [n["name"] for n in screens]))
            screens = [by_name[f] for f in a.frames]
        if not screens:
            sys.exit("no top-level frames on page %r" % page["name"])
        skipped = [{"name": n["name"], "type": n["type"]} for n in top if n not in screens]

        written = []
        if a.one_pdf:
            refuse_existing([out], a.overwrite)
            if skipped:
                aside = s.cmd("page.add", {"name": "_fc_export_aside"})["id"]
                s.cmd("object.moveToPage", {"ids": [n["id"] for n in top if n not in screens], "page": aside})
            res = s.cmd("file.exportFramesPdf", dict(print_opts, path=out, page=page["id"]))
            written.append({"path": out, "pages": res.get("pages"), "frames": [n["name"] for n in screens]})
        else:
            seen = {}
            for n in screens:
                seen[n["name"]] = seen.get(n["name"], 0) + 1
                name = n["name"].replace("/", "-") + ("" if seen[n["name"]] == 1 else " %d" % seen[n["name"]])
                path = os.path.join(out, "%s%s.%s" % (name, a.suffix, a.format))
                refuse_existing([path], a.overwrite)
                args = {"ids": [n["id"]], "path": path, "format": a.format}
                if a.format in ("png", "jpg", "webp"):
                    args["scale"] = a.scale
                if a.format == "pdf":
                    args.update(print_opts)
                res = s.tool("export", args)
                written.append({"path": path, "frame": n["name"], "bytes": res.get("bytes")})
    finally:
        s.close()
    print(json.dumps({"page": page["name"], "written": written, "skipped": skipped}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
