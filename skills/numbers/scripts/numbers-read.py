#!/usr/bin/env python3
"""Read a Numbers document back through Numbers itself: sheets, tables, values as
Numbers recalculated them, formatted values, formulas and error cells.

  python3 numbers-read.py budget.numbers                 every table as a grid
  python3 numbers-read.py budget.numbers --totals        totals per table
  python3 numbers-read.py budget.numbers --json          everything, machine-readable
  python3 numbers-read.py b.numbers --table Costs --cells B7 C7

Works for anything Numbers opens (.numbers, .xlsx, .csv), always read-only: the
document is closed without saving. Formula text comes back in the UI language
(=SZUM(...) under Hungarian), so compare values, not formula text.
Standard library only (python3 3.9).
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from numbers_osa import (  # noqa: E402
    NumbersError, addr, check_numbers_file, col_letter, parse_addr, real, run_ops)


def read_doc(path, sheets=None, tables=None, max_rows=None):
    p = real(path)
    check_numbers_file(p)
    return run_ops("read", {"path": p, "sheets": sheets or [], "tables": tables or [],
                            "maxRows": max_rows or 0}, docs=[p])


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def column_names(t):
    """Last header row's text per column, else the column letter."""
    names = []
    for c in range(t["columns"]):
        name = ""
        if t["headerRows"]:
            v = t["values"][t["headerRows"] - 1][c]
            name = "" if v is None else str(v)
        names.append(name or col_letter(c + 1))
    return names


def table_totals(t):
    """Footer row values when the table has a footer; else column sums of the body.
    -> (source, [(column name, value, cell)])"""
    names = column_names(t)
    hc = t["headerColumns"]
    if t["footerRows"]:
        r = t["rows"] - 1  # the last footer row carries the totals by convention
        out = [(names[c], t["values"][r][c], addr(r + 1, c + 1))
               for c in range(hc, t["columns"]) if is_num(t["values"][r][c])]
        return "footer row %d" % (r + 1), out
    body = t["values"][t["headerRows"]:t["rows"] - t["footerRows"]]
    out = []
    for c in range(hc, t["columns"]):
        nums = [row[c] for row in body if is_num(row[c])]
        if nums:
            out.append((names[c], round(sum(nums), 10), None))
    return "sum of body rows %d-%d" % (t["headerRows"] + 1, t["rows"] - t["footerRows"]), out


def fmt_num(v):
    if is_num(v) and float(v).is_integer():
        return str(int(v))
    return str(v)


def print_grid(t, max_rows):
    rows = t["formatted"][:max_rows] if max_rows else t["formatted"]
    width = [0] * t["columns"]
    for row in rows:
        for c, v in enumerate(row):
            width[c] = min(max(width[c], len("" if v is None else str(v))), 24)
    print("     " + "  ".join(col_letter(c + 1).ljust(width[c]) for c in range(t["columns"])))
    for i, row in enumerate(rows):
        cells = ["" if v is None else str(v)[:24] for v in row]
        print("%4d " % (i + 1) + "  ".join(v.ljust(width[c]) for c, v in enumerate(cells)))
    if t["truncated"] or (max_rows and t["rows"] > max_rows):
        print("     ... %d rows in total" % t["rows"])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--sheet", action="append", help="only this sheet (repeatable)")
    ap.add_argument("--table", action="append", help="only this table (repeatable)")
    ap.add_argument("--totals", action="store_true",
                    help="per table: its footer row, or the sums of its numeric columns")
    ap.add_argument("--cells", nargs="+", metavar="A1", help="print just these cells per table")
    ap.add_argument("--max-rows", type=int, default=50,
                    help="grid rows to print (0 = all; --json and --totals read everything)")
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()
    status = 0
    results = []
    for path in ns.paths:
        try:
            limit = ns.max_rows if not (ns.json or ns.totals or ns.cells) else 0
            doc = read_doc(path, ns.sheet, ns.table, limit)
        except NumbersError as e:
            print("error: %s: %s" % (path, e), file=sys.stderr)
            status = 1
            continue
        if ns.json:
            results.append(doc)
            continue
        print("== %s" % doc["path"])
        for s in doc["sheets"]:
            for t in s["tables"]:
                head = "%s / %s" % (s["name"], t["name"])
                if ns.totals:
                    src, tots = table_totals(t)
                    body = ", ".join("%s=%s" % (n, fmt_num(v)) for n, v, _ in tots) or "no numbers"
                    print("%s: %s  (%s)" % (head, body, src))
                    continue
                if ns.cells:
                    for a in ns.cells:
                        r, c = parse_addr(a)
                        if r > t["rows"] or c > t["columns"]:
                            print("%s!%s: outside the table" % (head, a))
                            continue
                        f = t["formulas"].get(a.upper())
                        print("%s!%s: %s  [%s]%s" % (head, a.upper(), t["values"][r - 1][c - 1],
                                                     t["formatted"][r - 1][c - 1],
                                                     "  " + f if f else ""))
                    continue
                print("-- %s  %d x %d, header rows %d, header columns %d, footer rows %d, "
                      "%d formulas%s" % (head, t["rows"], t["columns"], t["headerRows"],
                                         t["headerColumns"], t["footerRows"], len(t["formulas"]),
                                         ", ERRORS in " + " ".join(t["errors"]) if t["errors"] else ""))
                print_grid(t, ns.max_rows)
            if s["charts"] and not (ns.totals or ns.cells):
                print("   (%s: %d chart(s); chart data is not scriptable)" % (s["name"], s["charts"]))
    if ns.json:
        print(json.dumps(results[0] if len(results) == 1 else results, ensure_ascii=False, indent=1))
    return status


if __name__ == "__main__":
    sys.exit(main())
