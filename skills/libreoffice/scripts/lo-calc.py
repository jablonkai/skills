#!/usr/bin/env python3
"""Read, fill and recalculate spreadsheets with LibreOffice Calc (xlsx, ods, xls, csv).

  python3 lo-calc.py read model.xlsx                         # sheets, errors, used ranges
  python3 lo-calc.py read model.xlsx --range Summary.B1:B9 --range Total
  python3 lo-calc.py read model.xlsx --grid --sheet Summary  # whole used area
  python3 lo-calc.py fill model.xlsx --csv data.csv --at Data.A2 --skip-header \\
      -o out.xlsx -o out.pdf --read Summary.B1:B9
  python3 lo-calc.py fill model.xlsx --set Inputs.B2=0.21 --formula "Summary.C9==SUM(C2:C8)" -o out.ods

Values come back RECALCULATED: every formula is recomputed by Calc (xlsx cached values
are ignored; --no-recalc shows them). Formulas are written in Excel syntax by default
(commas, Sheet!A1); --native-formulas takes Calc's own (semicolons, $Sheet.A1).
Cell references: Sheet.A1, Sheet!A1, 'My sheet'.A1:B4, a named range, or A1 on the
first sheet. The source is never modified; results go to -o files (xlsx, ods, xls,
pdf, csv, html). fill exits 1 when any formula in the workbook evaluates to an error,
unless --allow-errors.
Standard library only (python3 3.9).
"""
import argparse
import csv
import datetime
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lo_run import (  # noqa: E402
    LOError, add_pdf_args, parse_typed, pdf_options, real, run_ops, sniff)

EPOCH = datetime.date(1899, 12, 30)  # Calc and Excel serial day 0


# ------------------------------------------------------------------ CSV parsing

def number(text, decimal, thousands):
    """float/int for a numeric CSV cell, else None. '1,250' -> 1250 only when it is a
    well-formed thousands grouping; leading-zero codes ('007') stay text."""
    t = text.strip()
    pct = t.endswith("%")
    if pct:
        t = t[:-1].strip()
    neg = t.startswith("-")
    body = t[1:] if neg else t
    if not body:
        return None
    th = re.escape(thousands) if thousands else None
    dec = re.escape(decimal)
    plain = r"\d+(?:%s\d+)?" % dec
    grouped = r"\d{1,3}(?:%s\d{3})+(?:%s\d+)?" % (th, dec) if th else None
    if re.fullmatch(plain, body):
        if len(body) > 1 and body[0] == "0" and body[1] != decimal:
            return None  # 007, 0123: codes, keep as text
    elif not (grouped and re.fullmatch(grouped, body)):
        return None
    if thousands:
        body = body.replace(thousands, "")
    if body.isdigit() and not pct:
        return -int(body) if neg else int(body)
    v = float(body.replace(decimal, "."))
    if pct:
        v /= 100
    return -v if neg else v


def read_rows(path, a):
    with open(path, "rb") as f:
        raw = f.read()
    text = raw.decode(a.encoding)
    if text.startswith("﻿"):
        text = text[1:]
    if path.lower().endswith(".json"):
        data = json.loads(text)
        if data and isinstance(data[0], dict):
            keys = list(data[0].keys())
            return [keys] + [[row.get(k) for k in keys] for row in data]
        return data
    delim = a.delimiter
    if not delim:
        try:
            delim = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|").delimiter
        except csv.Error:
            delim = ","
    rows = list(csv.reader(io.StringIO(text), delimiter=delim))
    out = []
    for row in rows:
        cells = []
        for c in row:
            if c == "":
                cells.append(None)
                continue
            if c.startswith("=") and a.csv_formulas:
                cells.append({"formula": c})
                continue
            v = number(c, a.decimal, a.thousands)
            if v is None and a.iso_dates and re.fullmatch(r"\d{4}-\d{2}-\d{2}", c.strip()):
                v = (datetime.date.fromisoformat(c.strip()) - EPOCH).days
            cells.append(c if v is None else v)
        out.append(cells)
    return out


# ------------------------------------------------------------------ output

def show(cell):
    if "e" in cell:
        return cell["e"]
    v = cell.get("v")
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def print_reads(reads, with_formulas=False):
    for rd in reads:
        print("== %s" % rd["range"])
        for row in rd["cells"]:
            cells = []
            for c in row:
                s = show(c)
                if with_formulas and c.get("f"):
                    s += "  [%s]" % c["f"]
                cells.append(s)
            print("\t".join(cells))


def print_errors(errors, count):
    if errors:
        print("ERRORS (%d of %d formulas):" % (len(errors), count))
        for e in errors:
            print("  %s  %s  %s" % (e["cell"], e["error"], e["formula"]))
    else:
        print("formulas: %d, no errors" % count)


# ------------------------------------------------------------------ commands

def cmd_read(a):
    src = real(a.file)
    bad = sniff(src, bool(a.password))
    if bad:
        raise LOError("%s: %s" % (src, bad))
    args = {"src": src, "recalc": not a.no_recalc, "read": a.range, "grid": a.grid,
            "sheets": a.sheet, "password": a.password}
    out = run_ops("calc_read", {k: v for k, v in args.items() if v not in (None, [])})
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 1 if out["errors"] else 0
    print("file: %s (%s)%s" % (src, out["import_filter"],
                               "" if a.no_recalc else ", recalculated"))
    for s in out["sheets"]:
        print("sheet %-24s used %s%s" % (s["name"], s["used"], "" if s["visible"] else "  (hidden)"))
        if "grid" in s:
            print_reads([s["grid"]], a.formulas)
    if out["named_ranges"]:
        print("named ranges: %s" % ", ".join(out["named_ranges"]))
    print_errors(out["errors"], out["formulas"])
    print_reads(out["reads"], a.formulas)
    return 1 if out["errors"] else 0


def parse_assign(text, what):
    if "=" not in text:
        raise LOError("%s wants CELL=VALUE, got %r" % (what, text))
    cell, value = text.split("=", 1)
    return cell.strip(), value


def cmd_fill(a):
    src = real(a.file)
    bad = sniff(src)
    if bad:
        raise LOError("%s: %s" % (src, bad))
    outs = [real(o) for o in a.output]
    for o in outs:
        if o == src:
            raise LOError("-o %s would overwrite the source; write to a new file" % o)
        if os.path.exists(o) and not a.force:
            raise LOError("%s exists (use --force)" % o)
    writes = []
    if a.csv:
        if not a.at:
            raise LOError("--csv needs --at, the top-left cell to write to (e.g. Data.A2)")
        rows = read_rows(real(a.csv), a)
        if a.skip_header and rows:
            rows = rows[1:]
        writes.append({"at": a.at, "rows": rows})
    sets = []
    for s in a.set:
        cell, value = parse_assign(s, "--set")
        sets.append({"cell": cell, "value": parse_typed(value) if value != "" else None})
    for s in a.set_text:
        cell, value = parse_assign(s, "--set-text")
        sets.append({"cell": cell, "value": value})
    for s in a.formula:
        cell, value = parse_assign(s, "--formula")
        if not value.startswith("="):
            value = "=" + value
        sets.append({"cell": cell, "value": {"formula": value}})
    pdf = pdf_options(a.pdfa, a.pdf_ua, a.pdf_opt)
    args = {"src": src, "writes": writes, "sets": sets, "clear": a.clear,
            "read": a.read, "syntax": "native" if a.native_formulas else "excel",
            "outputs": [{"dst": o, "pdf": pdf if o.lower().endswith(".pdf") else None}
                        for o in outs]}
    out = run_ops("calc_fill", args)
    for o in outs:
        if not os.path.exists(o):
            raise LOError("export missing: %s" % o)
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        for w in out["written"]:
            print("wrote %s" % w)
        print_errors(out["errors"], out["formulas"])
        print_reads(out["reads"], a.formulas)
        for o in out["outputs"]:
            print("saved %s (%s)" % (o["dst"], o["filter"]))
    return 1 if out["errors"] and not a.allow_errors else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("read", help="sheets, recalculated values, formula errors")
    r.add_argument("file")
    r.add_argument("--range", action="append", default=[], help="cells to print (repeat)")
    r.add_argument("--grid", action="store_true", help="print each sheet's used area")
    r.add_argument("--sheet", action="append", help="limit --grid to these sheets")
    r.add_argument("--formulas", action="store_true", help="show formulas next to values")
    r.add_argument("--no-recalc", action="store_true",
                   help="show the values stored in the file instead of recalculating")
    r.add_argument("--password")
    r.add_argument("--json", action="store_true")

    f = sub.add_parser("fill", help="write data, recalculate, export")
    f.add_argument("file", help="the workbook or template (never modified)")
    f.add_argument("-o", "--output", action="append", default=[], required=True,
                   help="output file; extension picks the format (repeat)")
    f.add_argument("--csv", help="CSV/TSV or JSON rows to write")
    f.add_argument("--at", help="top-left cell for --csv, e.g. Data.A2")
    f.add_argument("--skip-header", action="store_true", help="drop the CSV's first row")
    f.add_argument("--delimiter", help="CSV delimiter (default: sniffed)")
    f.add_argument("--decimal", default=".", help="CSV decimal mark (default .)")
    f.add_argument("--thousands", default=",", help="CSV thousands separator ('' for none)")
    f.add_argument("--encoding", default="utf-8")
    f.add_argument("--iso-dates", action="store_true",
                   help="YYYY-MM-DD cells become date serials (format the column as a date)")
    f.add_argument("--csv-formulas", action="store_true",
                   help="CSV cells starting with = become formulas (default: text)")
    f.add_argument("--clear", action="append", default=[],
                   help="range to empty before writing, e.g. Data.A2:D500 (repeat)")
    f.add_argument("--set", action="append", default=[], metavar="CELL=VALUE",
                   help="number/boolean/text into a cell (repeat)")
    f.add_argument("--set-text", action="append", default=[], metavar="CELL=TEXT",
                   help="text into a cell, never parsed as a number (repeat)")
    f.add_argument("--formula", action="append", default=[], metavar="CELL==EXPR",
                   help="formula into a cell, e.g. 'Summary.B9==SUM(B2:B8)' (repeat)")
    f.add_argument("--native-formulas", action="store_true",
                   help="formulas use Calc syntax (; and $Sheet.A1) instead of Excel's")
    f.add_argument("--read", action="append", default=[], help="range to print after recalc")
    f.add_argument("--formulas", action="store_true", help="show formulas next to values")
    f.add_argument("--allow-errors", action="store_true", help="exit 0 despite formula errors")
    f.add_argument("--force", action="store_true", help="overwrite existing outputs")
    f.add_argument("--json", action="store_true")
    add_pdf_args(f)

    a = ap.parse_args()
    if a.cmd == "fill" and a.thousands == a.decimal:
        raise LOError("--thousands and --decimal must differ")
    return cmd_read(a) if a.cmd == "read" else cmd_fill(a)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except LOError as e:
        print("error: %s" % e, file=sys.stderr)
        sys.exit(1)
