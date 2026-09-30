#!/usr/bin/env python3
"""Check a .numbers, .xlsx or .csv file against assertions. Exit 0 when all pass.

  python3 numbers-verify.py sales.numbers --tables 1 --formula B14 --expect B14=1250 --no-errors
  python3 numbers-verify.py sales.xlsx --numbers-coords --expect B14=1250 --formula B14
  python3 numbers-verify.py out.csv --expect B3=7

--expect [SHEET/TABLE!]CELL=VALUE compares numbers within --tol, else as text. In a
.numbers file SHEET/TABLE picks the table (default: the first); in an .xlsx it is the
worksheet name. XLSX values are the cached results Numbers wrote at export, read
straight from the zip. --numbers-coords shifts row numbers down one, past the table
name Numbers puts in row 1 of every exported worksheet, so the addresses you used in
Numbers still work. Standard library only (python3 3.9).
"""
import argparse
import csv
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from numbers_osa import NumbersError, addr, parse_addr  # noqa: E402

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"


class Book:
    """{sheet name: {A1: (value, formula or None)}}, sheet order, and error cells."""

    def __init__(self):
        self.sheets = {}
        self.order = []
        self.errors = []
        self.tables = 0
        self.charts = 0


def load_numbers(path):
    from importlib import import_module
    doc = import_module("numbers-read").read_doc(path)
    b = Book()
    for s in doc["sheets"]:
        b.charts += s["charts"]
        for t in s["tables"]:
            b.tables += 1
            key = "%s/%s" % (s["name"], t["name"])
            cells = {}
            for r, row in enumerate(t["values"]):
                for c, v in enumerate(row):
                    a = addr(r + 1, c + 1)
                    cells[a] = (v, t["formulas"].get(a))
            b.sheets[key] = cells
            b.order.append(key)
            b.errors += ["%s!%s" % (key, a) for a in t["errors"]]
    b.sheet_count = len(doc["sheets"])
    return b


def load_xlsx(path):
    b = Book()
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
                shared.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
        rels = {r.get("Id"): r.get("Target")
                for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels")).iter(REL + "Relationship")}
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        for sh in wb.find("m:sheets", NS):
            name = sh.get("name")
            target = rels[sh.get("{%s}id" % NS["r"])].lstrip("/")
            target = target if target.startswith("xl/") else "xl/" + target
            cells = {}
            for c in ET.fromstring(z.read(target)).iter("{%s}c" % NS["m"]):
                t, v, f = c.get("t"), c.find("m:v", NS), c.find("m:f", NS)
                val = None
                if t == "inlineStr":
                    val = "".join(x.text or "" for x in c.iter("{%s}t" % NS["m"]))
                elif v is not None and v.text is not None:
                    if t == "s":
                        val = shared[int(v.text)]
                    elif t in ("str", "e"):
                        val = v.text
                    elif t == "b":
                        val = v.text == "1"
                    else:
                        val = float(v.text)
                        val = int(val) if val.is_integer() else val
                if t == "e":
                    b.errors.append("%s!%s" % (name, c.get("r")))
                cells[c.get("r")] = (val, f.text if f is not None else None)
            b.sheets[name] = cells
            b.order.append(name)
        b.charts = len([n for n in z.namelist() if n.startswith("xl/charts/chart")])
    b.tables = b.sheet_count = len(b.order)
    return b


def load_csv(path):
    b = Book()
    with open(path, encoding="utf-8-sig", newline="") as fh:
        text = fh.read()
    try:
        delim = csv.Sniffer().sniff(text[:8192], delimiters=",;\t").delimiter
    except csv.Error:
        delim = ","
    cells = {}
    for r, row in enumerate(csv.reader(text.splitlines(), delimiter=delim)):
        for c, v in enumerate(row):
            if v != "":
                cells[addr(r + 1, c + 1)] = (v, None)
    b.sheets[os.path.basename(path)] = cells
    b.order.append(os.path.basename(path))
    b.tables = b.sheet_count = 1
    return b


def as_number(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(" ", "").replace(" ", "")
    s = re.sub(r"[^\d,.\-+eE%]", "", s)  # currency symbols, units
    if not s:
        return None
    if "," in s and "." not in s:
        s = s.replace(",", ".")
    else:
        s = s.replace(",", "")
    pct = s.endswith("%")
    try:
        n = float(s.rstrip("%"))
    except ValueError:
        return None
    return n / 100 if pct else n


def lookup(book, ref, shift):
    if "!" in ref:
        sheet, cell = ref.rsplit("!", 1)
        if sheet not in book.sheets:
            raise NumbersError("no sheet/table %r (have: %s)" % (sheet, ", ".join(book.order)))
    else:
        sheet, cell = book.order[0], ref
    r, c = parse_addr(cell)
    return book.sheets[sheet].get(addr(r + shift, c), (None, None)), "%s!%s" % (sheet, addr(r + shift, c))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path")
    ap.add_argument("--expect", action="append", default=[], metavar="[SHEET!]CELL=VALUE")
    ap.add_argument("--formula", action="append", default=[], metavar="[SHEET!]CELL",
                    help="the cell holds a formula, not a literal")
    ap.add_argument("--sheets", type=int, help=".numbers: sheet count; .xlsx: worksheet count")
    ap.add_argument("--tables", type=int, help="table count (xlsx: worksheets)")
    ap.add_argument("--no-errors", action="store_true", help="no formula evaluates to an error")
    ap.add_argument("--contains", action="append", default=[], help="some cell has this text")
    ap.add_argument("--tol", type=float, default=1e-6)
    ap.add_argument("--numbers-coords", action="store_true",
                    help="xlsx: addresses are the Numbers table's (skip the title row)")
    ns = ap.parse_args()
    ext = os.path.splitext(ns.path)[1].lower()
    try:
        if ext == ".xlsx":
            book = load_xlsx(ns.path)
        elif ext in (".csv", ".tsv"):
            book = load_csv(ns.path)
        else:
            book = load_numbers(ns.path)
    except (NumbersError, OSError, KeyError, ET.ParseError, zipfile.BadZipFile) as e:
        print("FAIL cannot read %s: %s" % (ns.path, e))
        return 1
    shift = 1 if ns.numbers_coords and ext == ".xlsx" else 0
    fails = 0

    def report(ok, msg):
        nonlocal fails
        print("%s %s" % ("PASS" if ok else "FAIL", msg))
        fails += 0 if ok else 1

    try:
        if ns.sheets is not None:
            report(book.sheet_count == ns.sheets, "sheets: %d (want %d)" % (book.sheet_count, ns.sheets))
        if ns.tables is not None:
            report(book.tables == ns.tables, "tables: %d (want %d)" % (book.tables, ns.tables))
        for spec in ns.expect:
            ref, want = spec.split("=", 1)
            (val, _), where = lookup(book, ref.strip(), shift)
            a, b = as_number(val), as_number(want)
            ok = (a is not None and b is not None and abs(a - b) <= ns.tol * max(1, abs(b))) \
                or str(val if val is not None else "") == want
            report(ok, "%s = %r (want %s)" % (where, val, want))
        for ref in ns.formula:
            (val, f), where = lookup(book, ref.strip(), shift)
            report(bool(f), "%s formula: %s (value %r)" % (where, f, val))
        if ns.no_errors:
            report(not book.errors, "error cells: %s" % (", ".join(book.errors) or "none"))
        for text in ns.contains:
            hit = any(text in str(v) for cells in book.sheets.values() for v, _ in cells.values()
                      if v is not None)
            report(hit, "contains %r" % text)
    except (NumbersError, ValueError) as e:
        print("FAIL %s" % e)
        return 1
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
