#!/usr/bin/env python3
"""Render one .ectemplate once per row of values — lower thirds, name titles, versions.

  ec_template.py T.ectemplate VALUES.(json|csv) OUTDIR [--format h264] [--still 2.0]
                 [--name "{Name}"] [--prores 4444 --channels rgba] [--overwrite] [--dry-run]

VALUES is a JSON array of objects or a CSV with a header row; keys are Essential Graphics
control names (case-insensitive, as essential.set matches them). A key `out` sets that
row's file name; otherwise --name (a str.format pattern over the row, default
"{index:02d}-{first value}") is slugged. Every key is checked against the template's
controls before anything renders, so a typo stops the run instead of rendering defaults.
--still T renders a PNG of time T instead of a movie. Prints a JSON report.
"""
import argparse
import csv
import json
import os
import re
import sys
import tempfile

from eclib import refuse_existing, run_cli

EXT = {"h264": "mp4", "hevc": "mp4", "av1": "mp4", "prores": "mov", "webm": "webm",
       "gif": "gif", "png": "png", "jpeg": "jpg", "tiff": "tif", "exr": "exr"}


def load_rows(path):
    if path.lower().endswith(".csv"):
        with open(path, newline="", encoding="utf-8-sig") as f:
            return [dict(r) for r in csv.DictReader(f)]
    with open(path, encoding="utf-8") as f:
        rows = json.load(f)
    if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
        sys.exit("ec_template: VALUES must be a JSON array of objects")
    return rows


def slug(text):
    return re.sub(r"[^A-Za-z0-9._-]+", "-", str(text)).strip("-") or "item"


def controls(template):
    t = json.loads(run_cli(["--empty", "exec", "essential.templateInfo", "--params",
                            json.dumps({"path": os.path.abspath(template)}), "--json"]).stdout)
    return t, [c["name"] for c in t.get("controls", []) if c.get("name")]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("template")
    ap.add_argument("values")
    ap.add_argument("outdir")
    ap.add_argument("--format", default="h264", choices=sorted(EXT))
    ap.add_argument("--still", type=float, help="render a PNG of this time (comp s) instead")
    ap.add_argument("--name", help='file-name pattern, e.g. "{Name}-{Title}"')
    ap.add_argument("--prores", help="ProRes profile: proxy|lt|standard|hq|4444|4444xq")
    ap.add_argument("--channels", choices=["rgb", "rgba"])
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="validate and list outputs only")
    a = ap.parse_args()

    manifest, names = controls(a.template)
    known = {n.lower() for n in names}
    rows = load_rows(a.values)
    if not rows:
        sys.exit("ec_template: no rows in %s" % a.values)
    unknown = sorted({k for r in rows for k in r if k != "out" and k.lower() not in known})
    if unknown:
        sys.exit("ec_template: unknown control(s) %s; the template has %s" % (unknown, names))

    ext = "png" if a.still is not None else EXT[a.format]
    jobs = []
    for i, row in enumerate(rows, 1):
        values = {k: v for k, v in row.items() if k != "out"}
        if row.get("out"):
            base = row["out"]
        elif a.name:
            base = a.name.format(index=i, **row)
        else:
            first = next(iter(values.values()), "")
            base = "%02d-%s" % (i, first)
        name = base if base.lower().endswith("." + ext) else slug(base) + "." + ext
        jobs.append((os.path.abspath(os.path.join(a.outdir, name)), values))
    outs = [o for o, _ in jobs]
    if len(set(outs)) != len(outs):
        sys.exit("ec_template: two rows map to the same file name; use --name or an out column")
    refuse_existing(outs, a.overwrite)

    report = {"template": os.path.abspath(a.template), "controls": names,
              "duration": manifest.get("duration"), "renders": []}
    if a.dry_run:
        report["renders"] = [{"out": o, "values": v} for o, v in jobs]
        print(json.dumps(report, indent=2))
        return
    os.makedirs(a.outdir, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for i, (out, values) in enumerate(jobs):
            vfile = os.path.join(tmp, "values-%d.json" % i)
            with open(vfile, "w", encoding="utf-8") as f:
                json.dump(values, f)
            if a.still is not None:
                args = ["render-frame", "--template", a.template, "--values", vfile,
                        "--time", str(a.still), "--out", out]
            else:
                args = ["render", "--template", a.template, "--values", vfile,
                        "--out", out, "--format", a.format]
                if a.prores:
                    args += ["--prores", a.prores]
                if a.channels:
                    args += ["--channels", a.channels]
            run_cli(args)
            report["renders"].append({"out": out, "values": values})
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        sys.exit("ec_template: %s" % e)
