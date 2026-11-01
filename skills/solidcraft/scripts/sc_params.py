#!/usr/bin/env python3
"""List or change a SolidCraft design's named parameters, on a copy, with read-back.

  sc_params.py bracket.solidcraft                       user parameters
  sc_params.py bracket.solidcraft --all                 also sketch dimensions (d1…) and feature inputs
  sc_params.py bracket.solidcraft --set wall="5 mm" hole_d=6 --save bracket-v2.solidcraft --out bracket-v2.step

--set names must already exist (user parameters, or dN sketch/feature inputs from
--all): `parameters.change {name}` with a misspelled name silently creates a new
parameter and leaves the model as it was, so this script checks every name first and
applies all values at once through `parameters.change {changes}`, which is all or
nothing. Then it saves the copy, exports, and reads both back with `solidcraft-cli
eval`: each changed parameter's new expression, no parameter added, no feature errors,
volume before and after, and each export's volume against the design's. Exits 1 on any
failed check. --expect-volume checks the new volume (±--tol %).
"""
import argparse
import json
import os
import sys

from sclib import Session, ToolError, evaluate, refuse_existing, sha256, summary


def parse_sets(items):
    out = {}
    for item in items:
        if "=" not in item:
            sys.exit("--set takes NAME=EXPR, got %r" % item)
        k, v = item.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("design")
    ap.add_argument("--all", action="store_true", help="list sketch and feature parameters too")
    ap.add_argument("--set", nargs="+", action="extend", default=[], metavar="NAME=EXPR")
    ap.add_argument("--save", help="the changed copy (.solidcraft); required with --set")
    ap.add_argument("--out", action="append", default=[], help="export the changed design (repeat)")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--expect-volume", type=float)
    ap.add_argument("--tol", type=float, default=0.5)
    a = ap.parse_args()

    dirs = {os.path.dirname(os.path.abspath(a.design))}
    if not a.set:
        s = Session(dirs)
        try:
            s.open(a.design)
            res = s.cmd("parameters.list", {"filter": "all" if a.all else "user"})
        finally:
            s.close()
        keep = ("name", "expression", "value", "unit", "source", "feature", "input", "comment", "error")
        print(json.dumps([{k: p.get(k) for k in keep if p.get(k) not in (None, "")}
                          for p in res.get("parameters", [])], indent=2, ensure_ascii=False))
        return

    if not a.save:
        ap.error("--set needs --save: the original is never changed")
    if os.path.realpath(a.save) == os.path.realpath(a.design):
        sys.exit("--save is the input file; write a copy instead")
    outs = [a.save] + a.out
    refuse_existing(outs, a.overwrite)
    changes = parse_sets(a.set)
    dirs |= {os.path.dirname(os.path.abspath(p)) for p in outs}
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    in_hash = sha256(a.design)
    before = summary(evaluate(a.design))
    s = Session(dirs)
    try:
        s.open(a.design)
        known = {p["name"]: p for p in s.cmd("parameters.list", {"filter": "all"}).get("parameters", [])}
        unknown = [n for n in changes if n not in known]
        if unknown:
            user = sorted(n for n, p in known.items() if p.get("source") in (None, "user"))
            sys.exit("no parameter named %s; user parameters: %s (sc_params.py %s --all lists the rest)"
                     % (", ".join(unknown), ", ".join(user) or "none", a.design))
        s.batch([{"command": "parameters.change", "params": {"changes": changes}}])
        s.save(a.save)
        for o in a.out:
            s.export(o)
    except ToolError as e:
        s.close()
        sys.exit("error: %s" % e)
    s.close()

    after = summary(evaluate(a.save))
    checks = []

    def check(name, ok, detail):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    all_after = {}
    s = Session(dirs)
    try:
        s.open(a.save)
        all_after = {p["name"]: p for p in s.cmd("parameters.list", {"filter": "all"}).get("parameters", [])}
    finally:
        s.close()
    for name, expr in changes.items():
        p = all_after.get(name) or {}
        got = p.get("expression")
        same = got is not None and got.replace(" ", "") == expr.replace(" ", "")
        try:  # a bare number is stored with the parameter's unit ("5" → "5 mm")
            same = same or abs(float(expr) - float(p.get("value"))) < 1e-9
        except (TypeError, ValueError):
            pass
        check("%s = %s" % (name, expr), same, "saved expression %r, value %s" % (got, p.get("value")))
    added = sorted(set(after["params"]) - set(before["params"]))
    check("no parameter added", not added, added or "none")
    check("no feature errors", not after["feature_errors"], after["feature_errors"] or "none")
    if a.expect_volume is not None:
        v = after["volume_mm3"]
        check("volume", v is not None and abs(v - a.expect_volume) <= abs(a.expect_volume) * a.tol / 100,
              "%s mm³, expected %s ±%s%%" % (v, a.expect_volume, a.tol))
    for o in a.out:
        if o.lower().endswith((".step", ".stp", ".stl", ".3mf", ".obj")) and os.path.isfile(o):
            v = summary(evaluate(o))["volume_mm3"]
            pct = 0.1 if o.lower().endswith((".step", ".stp")) else 1.0
            ref = after["volume_mm3"]
            check("volume of " + o, v is not None and ref and abs(v - ref) <= ref * pct / 100,
                  "%s vs %s mm³" % (v, ref))
        else:
            check("written " + o, os.path.isfile(o), o)
    check("input unchanged", sha256(a.design) == in_hash, a.design)

    report = {
        "changed": changes,
        "volume_before_mm3": before["volume_mm3"], "volume_after_mm3": after["volume_mm3"],
        "size_after": after["bodies"] and after["bodies"][0]["size"],
        "params_after": after["params"],
        "checks": checks, "ok": all(c["ok"] for c in checks),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
