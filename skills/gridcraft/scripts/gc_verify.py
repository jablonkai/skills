#!/usr/bin/env python3
"""Read a GridCraft workbook back and assert what a job promised. Prints JSON, exits 1 on a failed check.

    gc_verify.py read  FILE [--sheet S] [--range A1:E5] [--formulas]
        raw (unformatted) values, or formulas, as JSON rows; the numbers to report
    gc_verify.py cells FILE [--sheet S] [--tol 1e-6]
                       [--value B2=1200]... [--formula E2==SUM(B2:D2)]...
                       [--has-formula E2:E6]... [--numfmt B2:E6=$]...
        --value       recalculated value (numeric compare within --tol, else exact text)
        --formula     exact formula text (case and spaces ignored)
        --has-formula every cell of the range holds a formula, not a typed number
        --numfmt      every cell's number-format code contains the text ($, %, 0.00, …)
    gc_verify.py charts FILE [--count N] [--kind bar|column|line|pie|…]
    gc_verify.py files DIR --ext pdf [--count N] [--min-pages 1] [--expect-text '$18,093.65']...
        for PDFs also reads the text (pdftotext) and fails on #### (a column too narrow
        for its numbers) or on missing expected text
"""
import argparse
import glob
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gclib import emit, info, run_commands  # noqa: E402


def col_num(letters):
    n = 0
    for ch in letters.upper():
        n = n * 26 + ord(ch) - 64
    return n


def col_name(n):
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def expand(rng):
    """A1:C3 -> [A1, B1, C1, A2, …]; a single cell -> [cell]."""
    parts = rng.replace("$", "").split(":")
    m1 = re.fullmatch(r"([A-Za-z]+)(\d+)", parts[0])
    m2 = re.fullmatch(r"([A-Za-z]+)(\d+)", parts[-1])
    if not m1 or not m2:
        sys.exit(f"not a cell range: {rng}")
    c1, c2 = sorted((col_num(m1.group(1)), col_num(m2.group(1))))
    r1, r2 = sorted((int(m1.group(2)), int(m2.group(2))))
    return [f"{col_name(c)}{r}" for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)]


def split_pair(arg, sep="="):
    if sep not in arg:
        sys.exit(f"expected CELL{sep}VALUE, got {arg}")
    k, v = arg.split(sep, 1)
    return k.strip(), v


def norm_formula(f):
    return re.sub(r"\s+", "", (f or "").lstrip("=")).upper()


def cmd_read(a):
    params = {"formulas": a.formulas}
    if a.range:
        params["range"] = a.range
    res = run_commands(a.file, [("sheet.read", params)], sheet=a.sheet)[0] or {}
    emit({"file": a.file, "sheet": res.get("sheet"), "range": res.get("range"), "values": res.get("values")}, True)


def cmd_cells(a):
    wanted = {}
    for v in a.value:
        cell, _ = split_pair(v)
        wanted.setdefault(cell.upper(), None)
    for v in a.formula:
        cell, _ = split_pair(v)
        wanted.setdefault(cell.upper(), None)
    for rng in a.has_formula:
        for c in expand(rng):
            wanted.setdefault(c, None)
    for v in a.numfmt:
        rng, _ = split_pair(v)
        for c in expand(rng):
            wanted.setdefault(c, None)
    if not wanted:
        sys.exit("nothing to check: give --value, --formula, --has-formula or --numfmt")
    cells = list(wanted)
    results = run_commands(a.file, [("cell.get", {"cell": c}) for c in cells], sheet=a.sheet)
    got = dict(zip(cells, results))
    checks = []

    def add(name, passed, detail):
        checks.append({"check": name, "passed": bool(passed), "detail": detail})

    for v in a.value:
        cell, exp = split_pair(v)
        r = got[cell.upper()] or {}
        actual = r.get("value")
        try:
            passed = abs(float(actual) - float(exp)) <= a.tol
        except (TypeError, ValueError):
            passed = str(actual) == exp
        add(f"value {cell}", passed, f"expected {exp}, got {actual} (shown as {r.get('text')!r})")
    for v in a.formula:
        cell, exp = split_pair(v)
        actual = (got[cell.upper()] or {}).get("formula")
        add(f"formula {cell}", norm_formula(actual) == norm_formula(exp), f"expected {exp}, got {actual}")
    for rng in a.has_formula:
        missing = [c for c in expand(rng) if not (got[c] or {}).get("formula")]
        add(f"has-formula {rng}", not missing, f"no formula in {missing}" if missing else "all formulas")
    for v in a.numfmt:
        rng, text = split_pair(v)
        bad = {c: ((got[c] or {}).get("style") or {}).get("num_fmt") for c in expand(rng)}
        bad = {c: f for c, f in bad.items() if text not in (f or "")}
        add(f"numfmt {rng} contains {text!r}", not bad, f"other formats: {bad}" if bad else "all match")
    emit({"file": a.file, "sheet": a.sheet, "checks": checks}, all(c["passed"] for c in checks))


def cmd_charts(a):
    charts = [dict(c, sheet=s["name"]) for s in info(a.file)["sheets"] for c in s.get("charts") or []]
    ok = True
    if a.count is not None and len(charts) != a.count:
        ok = False
    if a.kind:
        ok = ok and any(c.get("kind", "").lower().startswith(a.kind.lower()) for c in charts)
    emit({"file": a.file, "charts": charts, "expected": {"count": a.count, "kind": a.kind}}, ok)


def pdf_pages(path):
    data = open(path, "rb").read()
    return len(re.findall(rb"/Type\s*/Page(?![s\w])", data))


def pdf_text(path):
    """Text of a PDF via pdftotext (poppler), or None when it isn't installed."""
    tool = shutil.which("pdftotext")
    if not tool:
        return None
    return subprocess.run([tool, "-layout", path, "-"], capture_output=True, text=True).stdout


def cmd_files(a):
    ext = a.ext.lower().lstrip(".")
    files = sorted(f for f in glob.glob(os.path.join(a.dir, "*")) if f.lower().endswith("." + ext))
    rows, ok = [], True
    for f in files:
        row = {"file": os.path.basename(f), "bytes": os.path.getsize(f)}
        if row["bytes"] == 0:
            ok = False
        if ext == "pdf":
            row["pages"] = pdf_pages(f)
            if row["pages"] < a.min_pages:
                ok = False
            text = pdf_text(f)
            if text is None:
                row["text"] = "not checked (install poppler for pdftotext)"
            else:
                row["overflow_cells"] = len(re.findall(r"#{3,}", text))
                row["missing_text"] = [t for t in a.expect_text if t not in text]
                if row["overflow_cells"] or row["missing_text"]:
                    ok = False
        rows.append(row)
    if a.count is not None and len(files) != a.count:
        ok = False
    emit({"dir": a.dir, "ext": ext, "count": len(files), "expected": a.count, "files": rows}, ok)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("read")
    p.add_argument("file")
    p.add_argument("--sheet")
    p.add_argument("--range")
    p.add_argument("--formulas", action="store_true")
    p = sub.add_parser("cells")
    p.add_argument("file")
    p.add_argument("--sheet")
    p.add_argument("--tol", type=float, default=1e-6)
    p.add_argument("--value", action="append", default=[])
    p.add_argument("--formula", action="append", default=[])
    p.add_argument("--has-formula", action="append", default=[])
    p.add_argument("--numfmt", action="append", default=[])
    p = sub.add_parser("charts")
    p.add_argument("file")
    p.add_argument("--count", type=int)
    p.add_argument("--kind")
    p = sub.add_parser("files")
    p.add_argument("dir")
    p.add_argument("--ext", required=True)
    p.add_argument("--count", type=int)
    p.add_argument("--min-pages", type=int, default=1)
    p.add_argument("--expect-text", action="append", default=[],
                   help="text every PDF must contain, e.g. a total as displayed ($18,093.65)")
    a = ap.parse_args()
    {"read": cmd_read, "cells": cmd_cells, "charts": cmd_charts, "files": cmd_files}[a.cmd](a)


if __name__ == "__main__":
    main()
