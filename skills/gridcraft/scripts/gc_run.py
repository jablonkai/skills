#!/usr/bin/env python3
"""Run a GridCraft step list in one gridcraft-cli process, save it, and summarise the result.

    gc_run.py [--in FILE | --sample budget|sales|grades] --out FILE [--print RANGE]
              [--overwrite] STEPS

STEPS is a .json file holding a list of {"command": id, "params": {...}}, a .jsonl file
(one `id={json}` or {"command", "params"} per line, # comments allowed), or `-` for a JSON
list on stdin. Without --in/--sample the steps start from a blank workbook.

Guards the silent failures of `gridcraft-cli run`: it refuses to run without --out (run
discards every change when --out is missing), refuses to overwrite an existing file or the
input unless --overwrite is given, and compares formula-cell counts before and after so a
command that wrote over existing formulas (e.g. table.totalRow) is reported. Exits 1 on a
failed step (nothing is saved then) or on lost formulas.
"""
import argparse
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gclib import XLSX_EXT, cli, info, json_lines, run_commands  # noqa: E402


def load_steps(src):
    text = sys.stdin.read() if src == "-" else open(src, encoding="utf-8").read()
    stripped = text.lstrip()
    if stripped.startswith("["):
        steps = json.loads(text)
        return [json.dumps({"command": s["command"], "params": s.get("params", {})}) for s in steps]
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith(("#", "//")):
            lines.append(line)
    return lines


def formula_counts(path):
    """Formula cells per sheet of a saved workbook (empty dict for non-xlsx input)."""
    if os.path.splitext(path)[1].lower() not in XLSX_EXT:
        return {}
    sheets = [s["name"] for s in info(path)["sheets"]]
    results = run_commands(path, [("sheet.read", {"sheet": s, "formulas": True}) for s in sheets])
    counts = {}
    for name, res in zip(sheets, results):
        values = (res or {}).get("values") or []
        counts[name] = sum(1 for row in values for v in row if isinstance(v, str) and v.startswith("="))
    return counts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--in", dest="inp")
    src.add_argument("--sample", choices=["budget", "sales", "grades"])
    ap.add_argument("--out", required=True, help="xlsx (default), .csv/.tsv/.json/.html/.pdf by extension")
    ap.add_argument("--print", dest="print_range")
    ap.add_argument("--overwrite", action="store_true", help="allow --out to replace an existing file or the input")
    ap.add_argument("steps")
    a = ap.parse_args()

    out = os.path.abspath(a.out)
    if a.inp and os.path.abspath(a.inp) == out and not a.overwrite:
        sys.exit("--out is the input file; pass --overwrite to save over it, or pick a new name")
    if os.path.exists(out) and not a.overwrite:
        sys.exit(f"{a.out} exists; pass --overwrite or pick a new name")

    lines = load_steps(a.steps)
    before = formula_counts(a.inp) if a.inp else {}

    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
        script = f.name
    args = ["run"]
    if a.inp:
        args += ["--in", a.inp]
    elif a.sample:
        args += ["--sample", a.sample]
    args += ["--script", script, "--out", a.out]
    if a.print_range:
        args += ["--print", a.print_range]
    proc = cli(*args)
    os.unlink(script)

    results = json_lines(proc.stdout)
    for r in results:
        res = json.dumps(r.get("result"), ensure_ascii=False)
        print(f"ok   {r.get('command')}: {res[:160]}")
    if proc.returncode != 0:
        print(f"FAIL {(proc.stderr or proc.stdout).strip()}")
        print(f"nothing saved; {len(results)} of {len(lines)} steps answered before the failure")
        sys.exit(1)
    if a.print_range:
        print("\n".join(l for l in proc.stdout.splitlines() if not l.startswith("{") and not l.startswith("wrote ")))
    print(f"saved {a.out}: {len(lines)} steps, {len(results)} answered with a result line "
          "(some commands, e.g. edit.autoFill, print none)")

    ok = True
    if os.path.splitext(out)[1].lower() in XLSX_EXT:
        meta = info(out)
        for s in meta["sheets"]:
            extras = [f"table {t.get('name')} {t.get('range')}" for t in s.get("tables") or []]
            extras += [f"chart {c.get('kind')} \"{c.get('title') or ''}\" at {c.get('at')}" for c in s.get("charts") or []]
            print(f"  sheet {s['name']}: used {s.get('usedRange')}" + (" | " + "; ".join(extras) if extras else ""))
        after = formula_counts(out)
        for name, n in before.items():
            if name in after and after[name] < n:
                ok = False
                print(f"LOST FORMULAS on {name}: {n} before, {after[name]} after; a step wrote over "
                      "formula cells (table.totalRow, setValues, paste?). Check before reporting.")
        print("formula cells: " + ", ".join(f"{k}={v}" for k, v in after.items()))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
