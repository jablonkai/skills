#!/usr/bin/env python3
"""Mail merge: one filled, exported document per data row.

  pages-merge.py TEMPLATE.pages DATA.csv|DATA.json --out-dir DIR
                 [--name '{last}_{first}.pdf'] [--format pdf] [--keep-pages]
                 [--token '{{%s}}'] [--image-col KEY=COLUMN]... [--dry-run]
                 [export options] [--force] [--allow-leftover]

Every column (CSV header, or key of each JSON object) fills the token {{column}}.
--name is a Python format string over the row; its extension, or --format, picks the
export format (pdf, docx, epub, rtf, txt). Default name: row-001.<format>.
--image-col swaps the image described as KEY for the file named in COLUMN.
--keep-pages also keeps each filled .pages next to its export.

The template is never edited. Rows are processed one at a time; a failing row is
reported and the rest continue. Exit 0 if every row succeeded, 1 otherwise.
Prints one JSON line per row, then a summary line.
"""
import argparse
import csv
import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pages_osa as po  # noqa: E402


def load_rows(path):
    if path.lower().endswith(".json"):
        with open(path, encoding="utf-8") as fh:
            rows = json.load(fh)
        if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
            raise po.PagesError("JSON data must be a list of objects")
    else:
        # utf-8-sig drops the BOM Excel writes; the sniffer handles ; and tab exports.
        with open(path, encoding="utf-8-sig", newline="") as fh:
            sample = fh.read(4096)
            fh.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
            except csv.Error:
                dialect = csv.excel
            rows = list(csv.DictReader(fh, dialect=dialect))
    clean = []
    for r in rows:
        clean.append({str(k).strip(): "" if v is None else str(v) for k, v in r.items() if k})
    return clean


def safe_name(name):
    name = re.sub(r'[/\\:\x00-\x1f]', "_", name).strip().strip(".")
    return name or "unnamed"


def main(argv):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("template")
    ap.add_argument("data")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--name", help="output file name pattern, e.g. '{name}.pdf'")
    ap.add_argument("--format", choices=po.FORMATS, help="export format (default: from --name, else pdf)")
    ap.add_argument("--keep-pages", action="store_true")
    ap.add_argument("--token", default="{{%s}}")
    ap.add_argument("--image-col", action="append", default=[], metavar="KEY=COLUMN")
    ap.add_argument("--dry-run", action="store_true", help="print planned outputs only")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--allow-leftover", action="store_true")
    po.add_export_args(ap)
    ns = ap.parse_args(argv)

    try:
        po.check_pages_file(ns.template)
        rows = load_rows(ns.data)
        if not rows:
            raise po.PagesError("no data rows in %s" % ns.data)
        image_cols = []
        for item in ns.image_col:
            if "=" not in item:
                raise po.PagesError("--image-col needs KEY=COLUMN")
            image_cols.append(tuple(item.split("=", 1)))
        fmt = ns.format
        if not fmt and ns.name and os.path.splitext(ns.name)[1]:
            fmt = po.format_of(ns.name)
        fmt = fmt or "pdf"
        out_dir = os.path.abspath(ns.out_dir)
        plan, seen = [], set()
        for i, row in enumerate(rows, 1):
            base = ns.name.format_map(dict(row, n=i)) if ns.name else "row-%03d" % i
            stem = safe_name(os.path.splitext(base)[0])
            name, k = stem, 2
            while name in seen:  # two rows with the same name must not overwrite
                name, k = "%s-%d" % (stem, k), k + 1
            seen.add(name)
            plan.append((i, row, os.path.join(out_dir, name + "." + fmt)))
    except (po.PagesError, KeyError, OSError, ValueError) as e:
        print(json.dumps({"ok": False, "error": "%s: %s" % (type(e).__name__, e)}, ensure_ascii=False))
        return 1 if not isinstance(e, KeyError) else 2

    if ns.dry_run:
        for i, row, out in plan:
            print(json.dumps({"row": i, "out": out, "values": row}, ensure_ascii=False))
        return 0

    os.makedirs(out_dir, exist_ok=True)
    opts = po.export_opt_args(ns)
    tmp = tempfile.mkdtemp(prefix="pages-merge-")
    failed = 0
    try:
        for i, row, out in plan:
            pages_out = os.path.splitext(out)[0] + ".pages"
            try:
                targets = [out] + ([pages_out] if ns.keep_pages else [])
                for t in targets:
                    if os.path.exists(t):
                        if not ns.force:
                            raise po.PagesError("exists (use --force): %s" % t)
                        po.remove_path(t)
                work = pages_out if ns.keep_pages else os.path.join(tmp, "row-%d.pages" % i)
                images = []
                for key, col in image_cols:
                    path = row.get(col, "")
                    if not os.path.isfile(path):
                        raise po.PagesError("row %d: image for %s not found: %r" % (i, key, path))
                    images.append((key, path))
                res = po.fill(ns.template, work, row, ns.token, images, (), [out], opts,
                              save=ns.keep_pages)
                ok = not (res["leftover"] and not ns.allow_leftover)
                line = {"row": i, "ok": ok, "out": out, "counts": res["counts"]}
                if res["leftover"]:
                    line["leftover"] = res["leftover"]
            except po.PagesError as e:
                ok, line = False, {"row": i, "ok": False, "out": out, "error": str(e)}
            failed += 0 if ok else 1
            print(json.dumps(line, ensure_ascii=False), flush=True)
    finally:
        po.remove_path(tmp)
    print(json.dumps({"ok": failed == 0, "rows": len(plan), "failed": failed, "out_dir": out_dir}))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
