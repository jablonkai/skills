#!/usr/bin/env python3
"""Export or batch-convert Numbers documents to XLSX, CSV, PDF or Numbers '09.

  python3 numbers-export.py budget.numbers --to xlsx
  python3 numbers-export.py ~/Reports -r --to xlsx --out-dir ~/Reports-xlsx
  python3 numbers-export.py a.numbers --to csv --flat-csv

Folders are searched for .numbers files (-r: recursively); the tree is mirrored
under --out-dir, or outputs land next to their sources. Existing outputs are skipped
unless --force. Sources are opened and closed without saving.

CSV: Numbers writes one CSV when the document has one table, else a folder X.csv/
holding "Sheet-Table.csv" per table (--flat-csv turns that into X-Sheet-Table.csv
files). Numbers' CSV uses the region's list separator (";" where "," is the decimal
mark) and formatted values ("33 Ft"); --raw-csv writes comma CSV of the raw values
instead. XLSX: one worksheet per table, the table name in row 1, so every address
moves down one row; the summary worksheet is left out unless --summary-worksheet.
Standard library only (python3 3.9).
"""
import argparse
import csv
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from numbers_osa import (  # noqa: E402
    EXPORT_AS, NumbersError, add_export_args, check_numbers_file, export_options, real,
    remove_path, run_ops)

BATCH = 10  # documents per osascript call: bounds the damage of one stuck file


def find_sources(paths, recursive):
    """-> [(source, relative path under its root)]; a .numbers package dir is a file."""
    out = []
    for p in paths:
        p = real(p)
        if p.lower().endswith(".numbers"):
            out.append((p, os.path.basename(p)))
            continue
        if not os.path.isdir(p):
            raise NumbersError("not a .numbers file or a folder: %s" % p)
        for root, dirs, files in os.walk(p):
            pkgs = [d for d in dirs if d.lower().endswith(".numbers")]
            for name in sorted(files + pkgs):
                if name.lower().endswith(".numbers") and not name.startswith("."):
                    full = os.path.join(root, name)
                    out.append((full, os.path.relpath(full, p)))
            dirs[:] = [] if not recursive else sorted(d for d in dirs if d not in pkgs)
    return out


def raw_csv(src, dst, flat):
    """Comma CSV of raw values per table, via numbers-read (no locale formatting)."""
    from importlib import import_module
    reader = import_module("numbers-read")
    doc = reader.read_doc(src)
    tables = [(s["name"], t) for s in doc["sheets"] for t in s["tables"]]
    outs = []
    if len(tables) == 1:
        outs.append((dst, tables[0][1]))
    else:
        stem = os.path.splitext(dst)[0]
        if not flat:
            os.makedirs(dst, exist_ok=True)
        for sname, t in tables:
            name = "%s-%s.csv" % (sname, t["name"])
            outs.append((stem + "-" + name if flat else os.path.join(dst, name), t))
    for path, t in outs:
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            for row in t["values"]:
                w.writerow(["" if v is None else (repr(v) if isinstance(v, float) else v)
                            for v in row])
    return {"src": src, "dst": dst, "ok": True, "sheets": len(doc["sheets"]),
            "tables": len(tables), "outs": [o for o, _ in outs]}


def flatten_csv(dst):
    """X.csv/ folder of per-table CSVs -> X-Sheet-Table.csv files beside it."""
    if not os.path.isdir(dst):
        return [dst]
    stem = os.path.splitext(dst)[0]
    moved = []
    for name in sorted(os.listdir(dst)):
        target = "%s-%s" % (stem, name)
        shutil.move(os.path.join(dst, name), target)
        moved.append(target)
    os.rmdir(dst)
    return moved


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sources", nargs="+", help=".numbers files and/or folders")
    ap.add_argument("--to", required=True, choices=sorted(EXPORT_AS))
    ap.add_argument("-r", "--recursive", action="store_true")
    ap.add_argument("--out-dir", help="mirror outputs under this folder")
    ap.add_argument("--out", help="output path (one source only)")
    ap.add_argument("--force", action="store_true", help="overwrite existing outputs")
    ap.add_argument("--flat-csv", action="store_true",
                    help="CSV of a multi-table document: X-Sheet-Table.csv files, not a folder")
    ap.add_argument("--raw-csv", action="store_true",
                    help="CSV: comma-separated raw values instead of Numbers' localized export")
    add_export_args(ap)
    ns = ap.parse_args()
    try:
        sources = find_sources(ns.sources, ns.recursive)
        if not sources:
            raise NumbersError("no .numbers files found")
        if ns.out and len(sources) != 1:
            raise NumbersError("--out needs exactly one source")
        as_name = EXPORT_AS[ns.to]
        opts = export_options(ns, as_name)
        items, skipped = [], 0
        for src, rel in sources:
            check_numbers_file(src)
            if ns.out:
                dst = real(ns.out)
            elif ns.out_dir:
                dst = os.path.join(real(ns.out_dir), os.path.splitext(rel)[0] + "." + ns.to)
            else:
                dst = os.path.splitext(src)[0] + "." + ns.to
            if os.path.exists(dst):
                if not ns.force:
                    print("SKIP %s (exists; --force to overwrite)" % dst)
                    skipped += 1
                    continue
                remove_path(dst)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            items.append({"src": src, "dst": dst})
    except NumbersError as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    results = []
    for i in range(0, len(items), BATCH):
        chunk = items[i:i + BATCH]
        try:
            if ns.to == "csv" and ns.raw_csv:
                for it in chunk:
                    results.append(raw_csv(it["src"], it["dst"], ns.flat_csv))
            else:
                results += run_ops("export", {"as": as_name, "options": opts, "items": chunk},
                                   docs=[it["src"] for it in chunk])
        except NumbersError as e:
            results += [dict(it, ok=False, error=str(e)) for it in chunk
                        if not any(r["src"] == it["src"] for r in results)]
    errors = 0
    for r in results:
        if not r["ok"]:
            errors += 1
            print("ERR  %s: %s" % (r["src"], r["error"]))
            continue
        outs = r.get("outs") or [r["dst"]]
        if ns.to == "csv" and ns.flat_csv and "outs" not in r:
            outs = flatten_csv(r["dst"])
        elif not all(os.path.exists(o) for o in outs):
            errors += 1
            print("ERR  %s: Numbers reported success but wrote nothing" % r["src"])
            continue
        print("OK   %s -> %s  (%d sheets, %d tables)" % (r["src"], ", ".join(outs),
                                                         r["sheets"], r["tables"]))
    print("%d exported, %d skipped, %d failed" % (len(results) - errors, skipped, errors))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
