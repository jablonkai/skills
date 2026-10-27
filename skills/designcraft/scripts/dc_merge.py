#!/usr/bin/env python3
"""Data-merge a DesignCraft template with CSV/TSV/XLSX records into one PDF (and/or document).

  dc_merge.py TEMPLATE.designcraft --pdf OUT.pdf [--data people.csv] [--save merged.designcraft]
              [--per-page multiple] [--row-spacing 10] [--column-spacing 10] [--range 1-20]
              [--png first.png --scale 2] [--pdf-options '{"standard":"x4","bleed":true}']
              [--allow-overset] [--overwrite] [--dry-run]

The template's placeholders (<<field>>) must all be columns of the data; the template's
own linked source is used when --data is left out. --per-page multiple tiles the records
on the template's single page (it must have one page with facing pages off): badges on A4
sheets. data.merge makes a new document; the template file is never written. Fails on
missing fields, overset records or missing images. Prints a JSON summary.
"""
import argparse
import json
import os
import re
import sys

from dclib import Session, ToolError, doc_json, field_names, refuse_existing, validate_pdf


def placeholders(template):
    dj = doc_json(template)
    fields = set()
    for st in dj["stories"].values():
        fields |= set(re.findall(r"<<([^<>]+)>>", st["text"]))
    srcs = (dj.get("dataMerge") or {}).get("sources") or []
    return fields, srcs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("template")
    ap.add_argument("--data")
    ap.add_argument("--pdf")
    ap.add_argument("--pdf-options", default="{}", help="extra file.exportPdf params as JSON")
    ap.add_argument("--save")
    ap.add_argument("--png", help="render the merged document's first page")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--per-page", choices=["single", "multiple"], default="single")
    ap.add_argument("--arrange", choices=["rows", "columns"])
    ap.add_argument("--row-spacing", type=float)
    ap.add_argument("--column-spacing", type=float)
    ap.add_argument("--range", help="records, 1-based: 1-20")
    ap.add_argument("--allow-overset", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="check fields, merge nothing")
    a = ap.parse_args()
    if not (a.pdf or a.save or a.dry_run):
        ap.error("give --pdf and/or --save (or --dry-run)")

    template = os.path.abspath(a.template)
    outs = [os.path.abspath(p) for p in (a.pdf, a.save, a.png) if p]
    refuse_existing(outs, a.overwrite)
    fields, srcs = placeholders(template)
    data = os.path.abspath(a.data) if a.data else (srcs[0].get("path") if srcs else None)
    if not data:
        sys.exit("the template links no data source; pass --data FILE")
    reads = {os.path.dirname(template), os.path.dirname(data)}
    s = Session(reads, {os.path.dirname(o) for o in outs} or {os.path.dirname(template)})
    try:
        s.tool("open_document", {"path": template})
        src = s.cmd("data.source.select", {"path": data})
        columns = field_names(src)
        missing = sorted(fields - set(columns))
        summary = {"template": template, "data": data, "records": src["records"],
                   "fields": columns, "placeholders": sorted(fields)}
        if missing:
            raise ToolError("placeholders %s are not columns of %s (columns: %s)" % (
                missing, os.path.basename(data), columns))
        if not fields:
            raise ToolError("the template has no <<field>> placeholders")
        if a.dry_run:
            print(json.dumps(summary, indent=2))
            return
        params = {"perPage": a.per_page}
        for key, val in (("arrange", a.arrange), ("rowSpacing", a.row_spacing),
                         ("columnSpacing", a.column_spacing)):
            if val is not None:
                params[key] = val
        if a.range:
            params.update({"records": "range", "range": a.range})
        merged = s.cmd("data.merge", params)
        summary["merge"] = merged
        if merged.get("oversetStories") and not a.allow_overset:
            raise ToolError("overset text in %s merged records; enlarge the frames or shorten "
                            "the text (or pass --allow-overset)" % merged["oversetStories"])
        if merged.get("missingImages"):
            raise ToolError("missing images: %s" % merged["missingImages"])
        if a.save:
            s.tool("save_document", {"path": os.path.abspath(a.save)})
            summary["saved"] = os.path.abspath(a.save)
        if a.png:
            s.tool("export_png", {"page": 0, "path": os.path.abspath(a.png), "scale": a.scale})
            summary["png"] = os.path.abspath(a.png)
        if a.pdf:
            opts = json.loads(a.pdf_options)
            opts["path"] = os.path.abspath(a.pdf)
            summary["pdf"] = s.cmd("file.exportPdf", opts)
    except ToolError as e:
        sys.exit("dc_merge: %s" % e)
    finally:
        s.close()
    if a.pdf and json.loads(a.pdf_options).get("standard") == "x4":
        v = validate_pdf(os.path.abspath(a.pdf))
        summary["validate"] = {"valid": v.get("valid"), "issues": v.get("issues")}
        if not v.get("valid"):
            print(json.dumps(summary, indent=2))
            sys.exit("PDF/X-4 validation failed")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
