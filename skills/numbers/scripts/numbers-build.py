#!/usr/bin/env python3
"""Build a Numbers table from CSV/TSV/JSON: typed values, header and footer rows,
column formats, formulas and an optional summary row, then export.

  python3 numbers-build.py sales.csv -o sales.numbers --summary-row SUM \\
      --format "B:E=currency" --export sales.xlsx

The CSV is parsed here, not by Numbers: Numbers' own CSV import follows the system
locale, so under a comma-decimal region "1,250" becomes 1.25 and "120.5" stays text.
Numbers are sent as numbers; text that Numbers would re-parse ("007", "1/2", "12%",
"2024-01-05") gets the text format first. Standard library only (python3 3.9).
"""
import argparse
import csv
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from numbers_osa import (  # noqa: E402
    FORMATS, NumbersError, add_export_args, addr, check_numbers_file, col_index,
    col_letter, export_as, export_options, parse_addr, real, remove_path, run_ops)

LOOKS_PARSED = re.compile(r"\d|^(true|false|yes|no)$", re.I)


def parse_number(s, dec, thou):
    """'1,250' -> 1250, '120.5' -> 120.5, '12%' -> (0.12, percent); else None.
    A leading zero ('007') stays text: the zeros would be lost."""
    t = s.strip()
    pct = t.endswith("%")
    if pct:
        t = t[:-1].strip()
    d, g = re.escape(dec), re.escape(thou) if thou else None
    grouped = r"\d{1,3}(?:%s\d{3})+" % g if g else None
    body = r"(?:%s|\d+)" % grouped if grouped else r"\d+"
    if not re.match(r"^[+-]?%s(?:%s\d+)?$|^[+-]?%s\d+$" % (body, d, d), t):
        return None
    digits = t.lstrip("+-")
    if len(digits) > 1 and digits[0] == "0" and digits[1] != dec:
        return None
    if thou:
        t = t.replace(thou, "")
    t = t.replace(dec, ".")
    v = float(t)
    if v.is_integer() and "." not in t:
        v = int(v)
    return (v / 100.0, "percent") if pct else (v, None)


def read_rows(path, ns):
    if path.lower().endswith(".json"):
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            data = data.get("rows") or data.get("data") or []
        if data and isinstance(data[0], dict):
            keys = []
            for obj in data:
                keys += [k for k in obj if k not in keys]
            return [keys] + [[obj.get(k) for k in keys] for obj in data], True
        return data, True
    with open(path, encoding=ns.encoding, newline="") as fh:
        text = fh.read()
    delim = ns.delimiter
    if delim in (None, ""):
        if path.lower().endswith((".tsv", ".tab")):
            delim = "\t"
        else:
            try:
                delim = csv.Sniffer().sniff(text[:8192], delimiters=",;\t|").delimiter
            except csv.Error:
                delim = ","
    elif delim == "tab":
        delim = "\t"
    rows = [r for r in csv.reader(io.StringIO(text), delimiter=delim)]
    while rows and not any(c.strip() for c in rows[-1]):
        rows.pop()
    return rows, False


def one_column(spec, header):
    if spec in header:
        return header.index(spec) + 1
    if re.match(r"^[A-Za-z]{1,3}$", spec):
        return col_index(spec)
    return None


def column_spec(spec, header, ncols):
    """'B', 'B:D', a header name or 'Q1:Q2' (two header names) -> 1-based columns,
    or None when spec is not a column spec (then it is taken as an A1 range)."""
    parts = [spec] if spec in header else spec.split(":")
    if len(parts) > 2:
        return None
    cols = [one_column(p.strip(), header) for p in parts]
    if None in cols:
        return None
    a, b = cols[0], cols[-1]
    if not 1 <= min(a, b) <= max(a, b) <= ncols:
        raise NumbersError("column %r is outside the table (1..%d columns)" % (spec, ncols))
    return list(range(min(a, b), max(a, b) + 1))


def plan(rows, is_json, ns):
    header_rows = min(ns.header_rows, len(rows))
    ncols = max((len(r) for r in rows), default=0)
    if ncols == 0:
        raise NumbersError("no data")
    body = rows[header_rows:]
    header = [str(c) if c is not None else "" for c in (rows[0] if header_rows else [])]
    writes, formats, formula_cells = [], [], []
    text_cells, numeric_cols = {}, set()
    thou = ns.thousands if ns.thousands != "none" else ""
    for ri, row in enumerate(rows):
        r = ri + 1
        for ci in range(ncols):
            c = ci + 1
            v = row[ci] if ci < len(row) else None
            if v is None or (isinstance(v, str) and v.strip() == ""):
                continue
            if isinstance(v, bool):
                writes.append([addr(r, c), "TRUE" if v else "FALSE"])
                text_cells.setdefault(c, []).append(r)
                continue
            if isinstance(v, (int, float)) and ri >= header_rows:
                writes.append([addr(r, c), v])
                numeric_cols.add(c)
                continue
            s = str(v)
            if ri >= header_rows and not is_json:
                num = parse_number(s, ns.decimal, thou)
                if num is not None:
                    writes.append([addr(r, c), num[0]])
                    numeric_cols.add(c)
                    if num[1]:
                        formats.append({"range": addr(r, c) + ":" + addr(r, c), "format": num[1]})
                    continue
            if s.startswith("=") and ns.csv_formulas:
                writes.append([addr(r, c), s])
                formula_cells.append(addr(r, c))
                continue
            writes.append([addr(r, c), s])
            # A text-format cell keeps "=..." as text, so CSV input can't inject formulas.
            if LOOKS_PARSED.search(s) or s.startswith("="):
                text_cells.setdefault(c, []).append(r)
    nrows = len(rows)
    data_first, data_last = header_rows + 1, nrows
    footer = 0
    if ns.summary_row:
        footer = 1
        nrows += 1
        label_done = False
        for c in range(1, ncols + 1):
            if c in numeric_cols and data_last >= data_first:
                rng = "%s:%s" % (addr(data_first, c), addr(data_last, c))
                writes.append([addr(nrows, c), "=%s(%s)" % (ns.summary_row, rng)])
                formula_cells.append(addr(nrows, c))
            elif not label_done:
                writes.append([addr(nrows, c), ns.summary_label])
                label_done = True
    extra = []
    for cell, expr in ns.formula or []:
        if not expr.startswith("="):
            expr = "=" + expr
        r, c = parse_addr(cell)
        nrows, ncols = max(nrows, r), max(ncols, c)
        extra.append([addr(r, c), expr])
        formula_cells.append(addr(r, c))
    writes += extra
    # Text format goes on before the values, so "007" is not entered as 7.
    for c, rs in text_cells.items():
        if c not in numeric_cols and len(rs) > 1:
            formats.insert(0, {"range": "%s:%s" % (addr(min(rs), c), addr(max(rs), c)),
                               "format": "text"})
        else:
            for r in rs:
                formats.insert(0, {"range": "%s:%s" % (addr(r, c), addr(r, c)), "format": "text"})
    for spec in ns.format or []:
        if "=" not in spec:
            raise NumbersError("--format wants RANGE=FORMAT, got %r" % spec)
        left, fmt = spec.rsplit("=", 1)
        fmt = fmt.strip().lower()
        if fmt == "date":
            fmt = "date and time"
        if fmt not in FORMATS:
            raise NumbersError("unknown format %r (use %s)" % (fmt, ", ".join(FORMATS)))
        left = left.strip()
        cols = column_spec(left, header, ncols)
        if cols is None:
            if not re.match(r"^[A-Za-z]+\d+(:[A-Za-z]+\d+)?$", left):
                raise NumbersError("no column or range %r (use a letter, B:D, a header name "
                                   "or an A1 range)" % left)
            rng = left if ":" in left else left + ":" + left
            for a in rng.split(":"):
                r, c = parse_addr(a)
                if r > nrows or c > ncols:
                    raise NumbersError("range %s is outside the table (%d x %d)"
                                       % (left, nrows, ncols))
            formats.append({"range": rng.upper(), "format": fmt})
            continue
        for c in cols:
            formats.append({"range": "%s:%s" % (addr(header_rows + 1, c), addr(nrows, c)),
                            "format": fmt})
    return {
        "rowCount": max(nrows, header_rows + footer + 1),
        "columnCount": ncols,
        "headerRows": header_rows,
        "headerCols": ns.header_cols,
        "footerRows": footer,
        "formats": formats,
        "writes": writes,
        "formulaCells": formula_cells,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="CSV, TSV or JSON (list of rows, or list of objects)")
    ap.add_argument("-o", "--out", required=True, help=".numbers to create (or to add to with --into)")
    ap.add_argument("--into", action="store_true",
                    help="add a table to the existing --out document instead of creating it: "
                         "onto sheet --sheet when it exists, else onto a new sheet")
    ap.add_argument("--force", action="store_true", help="replace an existing --out")
    ap.add_argument("--sheet", help="sheet name")
    ap.add_argument("--table", help="table name")
    ap.add_argument("--header-rows", type=int, default=1)
    ap.add_argument("--header-cols", type=int, default=0)
    ap.add_argument("--delimiter", help="CSV delimiter: , ; | or tab (default: sniffed)")
    ap.add_argument("--decimal", default=".", help="decimal mark in the CSV (default .)")
    ap.add_argument("--thousands", help="grouping mark in the CSV, or none "
                    "(default , when --decimal is ., else none)")
    ap.add_argument("--encoding", default="utf-8-sig")
    ap.add_argument("--summary-row", nargs="?", const="SUM", metavar="FUNC",
                    help="append a footer row with FUNC(column) for every numeric column "
                         "(default SUM; AVERAGE, MIN, MAX, COUNT, ...)")
    ap.add_argument("--summary-label", default="Total")
    ap.add_argument("--formula", nargs=2, action="append", metavar=("CELL", "EXPR"),
                    help="set CELL to formula EXPR (English function names, e.g. '=B2*C2'); "
                         "the table grows to include CELL")
    ap.add_argument("--format", action="append", metavar="RANGE=FORMAT",
                    help="column letter(s) B or B:D, a header name, or an A1 range, = one of "
                         + ", ".join(FORMATS) + " (date = date and time)")
    ap.add_argument("--csv-formulas", action="store_true",
                    help="enter CSV cells that start with = as formulas (default: kept as text)")
    ap.add_argument("--export", action="append", default=[], metavar="PATH",
                    help="also export to PATH (.xlsx, .csv, .pdf, .numbers09); repeatable")
    ap.add_argument("--json", action="store_true", help="print the result as JSON")
    add_export_args(ap)
    ns = ap.parse_args()
    if ns.thousands is None:
        ns.thousands = "," if ns.decimal == "." else "none"
    if ns.summary_row:
        ns.summary_row = ns.summary_row.upper()
    try:
        out = real(ns.out)
        if not out.lower().endswith(".numbers"):
            raise NumbersError("--out must end in .numbers")
        if ns.into:
            check_numbers_file(out)
        elif os.path.exists(out):
            if not ns.force:
                raise NumbersError("%s exists (use --force to replace, --into to add a table)" % out)
            remove_path(out)
        rows, is_json = read_rows(ns.input, ns)
        req = plan(rows, is_json, ns)
        cells = len(req["writes"])
        if cells > 5000:
            print("note: %d cells, about %d s (one Apple event per cell)" % (cells, cells // 50),
                  file=sys.stderr)
        exports = []
        for p in ns.export:
            p = real(p)
            if os.path.exists(p):
                if not ns.force:
                    raise NumbersError("%s exists (use --force)" % p)
                remove_path(p)
            as_name = export_as(p)
            exports.append({"path": p, "as": as_name, "options": export_options(ns, as_name)})
        req.update({"out": out, "into": ns.into, "sheet": ns.sheet, "table": ns.table,
                    "exports": exports})
        res = run_ops("build", req, docs=[out])
    except (NumbersError, OSError, ValueError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    if ns.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
        return 0
    print("built %s: %s / %s, %d x %d" % (res["out"], res["sheet"], res["table"],
                                          res["rows"], res["columns"]))
    for f in res["formulas"]:
        state = "ERROR" if f["error"] else f["value"]
        print("  %s %s -> %s (%s)" % (f["cell"], f["formula"], state, f["formatted"]))
    for p in res["exports"]:
        print("exported %s" % p)
    return 1 if any(f["error"] for f in res["formulas"]) else 0


if __name__ == "__main__":
    sys.exit(main())
