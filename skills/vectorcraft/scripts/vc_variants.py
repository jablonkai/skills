#!/usr/bin/env python3
"""Render one file per CSV row from a VectorCraft template via variables and data sets.

    vc_variants.py TEMPLATE CSV OUT_DIR [--bind KIND:VAR=REF ...] [--map COL=VAR ...]
                   [--name-col COL] [--ext png] [--scale N] [--artboard I]
                   [--pattern "{row}"] [--save-template FILE] [--overwrite]

TEMPLATE  any readable file (.vectorcraft, .vctemplate, .svg, .ai, .pdf…); never written.
--bind    define a variable and bind an object to it, e.g.
          text:Headline=@name:Title   visibility:ShowBadge=@name:Badge
          image:Photo=@name:Photo     (REF: @name:…, @text:… or a numeric id)
          Skip it when the template already has its variables (variable.list).
--map     CSV column -> variable (default: a column feeds the variable of the same name).
--name-col the column naming each row/output (default: the first column).
Visibility cells accept true/false, yes/no, 1/0, show/hide.
Each row is applied with dataset.select, then exported as OUT_DIR/<pattern>.<ext>;
--pattern takes {row} (the --name-col value) and {<any column>}.
Prints a JSON report with each output and any text overflow; exits 1 on error.
The data sets are recorded in --save-template (rows named row1, row2…).
"""
import argparse
import csv
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vclib import Session, ToolError, refuse_existing  # noqa: E402

TRUE = {"true", "yes", "y", "1", "show", "shown", "visible", "on"}
FALSE = {"false", "no", "n", "0", "hide", "hidden", "off", ""}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("template")
    ap.add_argument("csv")
    ap.add_argument("outdir")
    ap.add_argument("--bind", nargs="+", default=[])
    ap.add_argument("--map", nargs="+", default=[])
    ap.add_argument("--name-col")
    ap.add_argument("--ext", default="png")
    ap.add_argument("--scale", type=float)
    ap.add_argument("--artboard", type=int)
    ap.add_argument("--pattern", default="{row}")
    ap.add_argument("--save-template")
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args()

    template = os.path.realpath(a.template)
    outdir = os.path.realpath(a.outdir)
    os.makedirs(outdir, exist_ok=True)
    with open(a.csv, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit("CSV has no rows")
    cols = list(rows[0].keys())
    name_col = a.name_col or cols[0]
    colmap = dict(m.split("=", 1) for m in a.map)

    outputs = []
    for r in rows:
        fields = {k: v for k, v in r.items() if k}
        fields["row"] = r[name_col]
        stem = a.pattern.format(**fields)
        outputs.append(os.path.join(outdir, "%s.%s" % (stem, a.ext.strip("."))))
    if len(set(outputs)) != len(outputs):
        sys.exit("output names collide: make --pattern unique per row")
    save = os.path.realpath(a.save_template) if a.save_template else None
    if save == template:
        sys.exit("--save-template must not be the template itself")
    refuse_existing(outputs + ([save] if save else []), a.overwrite)

    read_root = os.path.commonpath([os.path.dirname(template), os.path.dirname(os.path.realpath(a.csv))])
    write_root = os.path.commonpath([outdir] + ([os.path.dirname(save)] if save else []))
    s = Session(read_root, write_root)
    report = {"outputs": []}
    try:
        s.tool("open_file", {"path": template})
        for spec in a.bind:
            kind, _, rest = spec.partition(":")
            var, _, ref = rest.partition("=")
            oid = int(ref) if ref.isdigit() else s.resolve(ref)
            s.cmd("variable.define", {"name": var, "kind": kind})
            s.cmd("variable.bind", {"variable": var, "ids": [oid]})
        variables = {v["name"]: v["kind"] for v in s.cmd("variable.list").get("variables", [])}
        if not variables:
            raise ToolError("the template has no variables: pass --bind")

        feeds = {}  # variable -> column
        for col in cols:
            var = colmap.get(col, col)
            if var in variables and col != name_col:
                feeds[var] = col
        missing = [v for v in variables if v not in feeds]
        if missing:
            raise ToolError("no CSV column for variable(s) %s; columns: %s (use --map COL=VAR)" % (missing, cols))

        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["name"] + list(feeds))
        for i, r in enumerate(rows):
            vals = []
            for var, col in feeds.items():
                v = (r.get(col) or "").strip()
                if variables[var] == "visibility":
                    low = v.lower()
                    if low not in TRUE | FALSE:
                        raise ToolError("row %d: %r is not a visibility value" % (i + 1, v))
                    v = "true" if low in TRUE else "false"
                vals.append(v)
            w.writerow(["row%d" % (i + 1)] + vals)
        s.cmd("dataset.import", {"csv": buf.getvalue()})

        for i, (r, out) in enumerate(zip(rows, outputs)):
            res = s.cmd("dataset.select", {"name": "row%d" % (i + 1)})
            args = {"path": out}
            if a.scale:
                args["scale"] = a.scale
            if a.artboard is not None:
                args["artboard"] = a.artboard
            exp = s.tool("export", args)
            entry = {"row": r[name_col], "path": out, "bytes": exp.get("bytes"),
                     "warnings": exp.get("warnings", [])}
            if res.get("overflow"):
                entry["overflow"] = res["overflow"]
            if res.get("warning"):
                entry["selectWarning"] = res["warning"]
            report["outputs"].append(entry)
        if save:
            report["template"] = s.tool("save_file", {"path": save})
    except ToolError as e:
        print(json.dumps({"error": str(e), "partial": report}, indent=1))
        return 1
    finally:
        s.close()
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
