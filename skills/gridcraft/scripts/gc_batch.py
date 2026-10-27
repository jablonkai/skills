#!/usr/bin/env python3
"""Folder batches for GridCraft: convert every workbook, or check every workbook and report.

    gc_batch.py convert IN_DIR OUT_DIR --to pdf|xlsx|csv|tsv|json|html
                        [--ext xlsx,csv] [--sheet NAME] [--recursive] [--overwrite]
        one `gridcraft-cli convert` per file; output keeps the stem (sub-folders mirrored with
        --recursive). Refuses to overwrite existing outputs unless --overwrite (convert itself
        overwrites silently). Exits 1 if any file failed.

    gc_batch.py check PATH... [--tolerance 1e-9] [--json]
        runs `gridcraft-cli check --json` and prints one verdict per workbook:
          clean         every formula with a cached value recalculated to it, round trip equal
          MISMATCH      a recalculated value differs from the cached one (cells listed)
          ROUND-TRIP    a save/reopen changed something (categories listed)
          NOT VERIFIED  formulas present but none had a usable cached value (e.g. written by
                        openpyxl) - this is not "clean"
          FAILED        the file could not be opened
        and lists files in the folders that check skipped (it reads .xlsx/.xlsm only).
        Exits 1 on any MISMATCH, ROUND-TRIP or FAILED.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gclib import cli  # noqa: E402

READABLE = {".xlsx", ".xlsm", ".xls", ".xlsb", ".ods", ".csv", ".tsv", ".txt", ".json"}


def walk(root, recursive):
    if recursive:
        for d, _, names in os.walk(root):
            for n in sorted(names):
                yield os.path.join(d, n)
    else:
        for n in sorted(os.listdir(root)):
            p = os.path.join(root, n)
            if os.path.isfile(p):
                yield p


def cmd_convert(a):
    exts = {"." + e.strip().lower().lstrip(".") for e in a.ext.split(",")} if a.ext else READABLE
    to = a.to.lower().lstrip(".")
    rows, failed = [], 0
    for src in walk(a.in_dir, a.recursive):
        base = os.path.basename(src)
        if base.startswith(("~$", ".")) or os.path.splitext(src)[1].lower() not in exts:
            continue
        rel = os.path.relpath(src, a.in_dir)
        dst = os.path.join(a.out_dir, os.path.splitext(rel)[0] + "." + to)
        if os.path.abspath(dst) == os.path.abspath(src):
            rows.append((rel, "SKIP", "same file as output"))
            continue
        if os.path.exists(dst) and not a.overwrite:
            rows.append((rel, "SKIP", f"{dst} exists (use --overwrite)"))
            continue
        os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
        args = ["convert", src, dst] + (["--sheet", a.sheet] if a.sheet else [])
        proc = cli(*args)
        if proc.returncode == 0 and os.path.exists(dst):
            msg = ((proc.stdout + proc.stderr).strip().splitlines() or [""])[-1]
            rows.append((rel, "ok", msg))
        else:
            failed += 1
            rows.append((rel, "FAIL", (proc.stderr or proc.stdout).strip()))
    for rel, status, msg in rows:
        print(f"{status:5} {rel}  {msg}")
    done = sum(1 for r in rows if r[1] == "ok")
    print(f"converted {done}, skipped {sum(1 for r in rows if r[1] == 'SKIP')}, failed {failed}")
    sys.exit(1 if failed else 0)


def verdict(f):
    if not f.get("opened") or f.get("error"):
        return "FAILED", f.get("error") or "could not open"
    calc = f.get("calc") or {}
    rt = f.get("roundTrip") or {}
    if calc.get("mismatched"):
        # check's "expected" is the value saved in the file, "actual" is GridCraft's recalculation
        cells = [f"{m['cell']} {m.get('formula')} saved {m.get('expected')} recalculated {m.get('actual')}"
                 for m in calc.get("mismatches", [])]
        return "MISMATCH", "; ".join(cells)
    if rt.get("differing") or rt.get("error"):
        return "ROUND-TRIP", ", ".join(rt.get("differing") or []) or str(rt.get("error"))
    if calc.get("formulaCells") and not calc.get("checked"):
        why = "stale cache flag set by the producer" if calc.get("staleCache") else "no cached values"
        return "NOT VERIFIED", f"{calc.get('formulaCells')} formulas, 0 checked ({why})"
    note = f"{calc.get('checked', 0)}/{calc.get('formulaCells', 0)} formulas checked"
    if calc.get("noOracle") or calc.get("volatile"):
        note += f", {calc.get('noOracle', 0)} no oracle, {calc.get('volatile', 0)} volatile"
    return "clean", note


def cmd_check(a):
    proc = cli("check", *a.paths, "--json", "--tolerance", str(a.tolerance), "--max-report", "1000")
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        sys.exit(f"check produced no JSON (exit {proc.returncode}): {(proc.stderr or proc.stdout).strip()}")
    files = data.get("files", [])
    checked = {os.path.abspath(f["path"]) for f in files}
    skipped = []
    for p in a.paths:
        if os.path.isdir(p):
            skipped += [os.path.relpath(x, p) for x in walk(p, True)
                        if os.path.abspath(x) not in checked and not os.path.basename(x).startswith(".")]
    rows = [(f["path"], *verdict(f)) for f in files]
    bad = any(v in ("MISMATCH", "ROUND-TRIP", "FAILED") for _, v, _ in rows)
    if a.json:
        print(json.dumps({"files": [{"path": p, "verdict": v, "detail": d} for p, v, d in rows],
                          "skipped": skipped, "totals": data.get("totals"), "ok": not bad}, indent=2))
    else:
        width = max([len(p) for p, _, _ in rows] + [4])
        for p, v, d in rows:
            print(f"{p:<{width}}  {v:<12}  {d}")
        if skipped:
            print(f"skipped by check (not .xlsx/.xlsm): {', '.join(skipped)}")
        t = data.get("totals") or {}
        print(f"files {t.get('files', len(rows))}: {t.get('mismatched', 0)} mismatched cells, "
              f"{t.get('roundTripDiffering', 0)} round-trip differences, {t.get('failedToOpen', 0)} failed to open")
    sys.exit(1 if bad else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("convert")
    p.add_argument("in_dir")
    p.add_argument("out_dir")
    p.add_argument("--to", required=True)
    p.add_argument("--ext")
    p.add_argument("--sheet")
    p.add_argument("--recursive", action="store_true")
    p.add_argument("--overwrite", action="store_true")
    p = sub.add_parser("check")
    p.add_argument("paths", nargs="+")
    p.add_argument("--tolerance", type=float, default=1e-9)
    p.add_argument("--json", action="store_true")
    a = ap.parse_args()
    {"convert": cmd_convert, "check": cmd_check}[a.cmd](a)


if __name__ == "__main__":
    main()
