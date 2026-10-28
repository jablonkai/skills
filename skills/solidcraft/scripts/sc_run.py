#!/usr/bin/env python3
"""Run a SolidCraft command script on a new design or on a copy of one, then read it back.

  sc_run.py SCRIPT --save part.solidcraft --out part.step --out part.stl
  sc_run.py edit.json --in bracket.solidcraft --save bracket-v2.solidcraft --out bracket-v2.step
  sc_run.py SCRIPT --save p.solidcraft --expect-volume 23420.1 --expect-size 60 40 10 --expect-bodies 1

SCRIPT is a file or inline JSON: {"commands": [{"command": ID, "params": {...}}, ...]}
(the format `solidcraft-cli run` and `script` use) or a bare list of steps.

The steps run in one headless MCP session with --param-check strict, as one
all-or-nothing batch: a misspelled key (`bodyname`) or a failing feature stops the run
before anything is applied or written. Then the design is saved and exported, and every
output is measured again by `solidcraft-cli eval`, independent of the session:
the saved design's bodies, volume, size, parameters and feature errors, and each
export's volume and size against the design's. Exits 1 on any failed check.

--in is opened, never written: --save must be a different path, and its hash is checked
before and after. Outputs are not overwritten without --overwrite.
"""
import argparse
import json
import os
import sys

from sclib import Session, ToolError, evaluate, load_script, refuse_existing, sha256, summary

MESH_EXT = (".stl", ".obj", ".3mf")
READBACK_EXT = (".solidcraft", ".step", ".stp") + MESH_EXT


def near(a, b, pct):
    return a is not None and b is not None and abs(a - b) <= abs(b) * pct / 100.0 + 1e-6


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script")
    ap.add_argument("--in", dest="inp", help="design or part to start from (.solidcraft, .step, .stl …)")
    ap.add_argument("--save", help="write the design here (.solidcraft)")
    ap.add_argument("--out", action="append", default=[], help="export by extension: .step .stl .3mf .obj .urdf (repeat)")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--expect-volume", type=float, help="total volume in mm³")
    ap.add_argument("--expect-size", type=float, nargs=3, metavar=("X", "Y", "Z"), help="overall bbox size in mm")
    ap.add_argument("--expect-bodies", type=int)
    ap.add_argument("--tol", type=float, default=0.5, help="volume tolerance in %% (default 0.5)")
    ap.add_argument("--size-tol", type=float, default=0.01, help="size tolerance in mm (default 0.01)")
    ap.add_argument("--json-out", help="also write the report here")
    a = ap.parse_args()

    if not (a.save or a.out):
        ap.error("give --save and/or --out: a run that writes nothing can't be read back")
    outs = ([a.save] if a.save else []) + a.out
    if a.inp and any(os.path.realpath(o) == os.path.realpath(a.inp) for o in outs):
        sys.exit("an output is the --in file; write a copy (e.g. NAME-v2.solidcraft) instead")
    if a.save and not a.save.endswith((".solidcraft", ".json")):
        sys.exit("--save takes a .solidcraft (or .json) path; use --out for exports")
    refuse_existing(outs, a.overwrite)
    steps = load_script(a.script)

    in_hash = sha256(a.inp) if a.inp else None
    dirs = {os.path.dirname(os.path.abspath(p)) or "." for p in outs}
    if a.inp:
        dirs.add(os.path.dirname(os.path.abspath(a.inp)))
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    report = {"steps": len(steps), "outputs": {}, "checks": []}
    s = Session(dirs)
    try:
        if a.inp:
            s.open(a.inp)
        if steps:
            s.batch(steps)
        if a.save:
            s.save(a.save)
        for o in a.out:
            s.export(o)
    except ToolError as e:
        s.close()
        sys.exit("error: %s" % e)
    s.close()

    def check(name, ok, detail):
        report["checks"].append({"check": name, "ok": bool(ok), "detail": detail})

    ref = None
    for o in outs:
        if not os.path.isfile(o):
            check("written " + o, False, "missing")
            continue
        if not o.lower().endswith(READBACK_EXT):
            check("written " + o, True, "%d bytes (not read back)" % os.path.getsize(o))
            continue
        sm = summary(evaluate(o))
        report["outputs"][o] = sm
        if ref is None:
            ref = sm
            continue
        pct = 1.0 if o.lower().endswith(MESH_EXT) else 0.1
        if ref["volume_mm3"]:
            check("volume of " + o, near(sm["volume_mm3"], ref["volume_mm3"], pct),
                  "%s vs %s mm³ (±%s%%)" % (sm["volume_mm3"], ref["volume_mm3"], pct))

    if ref:
        size = [max(b["bbox_max"][i] for b in ref["bodies"]) - min(b["bbox_min"][i] for b in ref["bodies"])
                for i in range(3)] if ref["bodies"] else [0, 0, 0]
        ref["overall_size"] = [round(v, 3) for v in size]
        check("no feature errors", not ref["feature_errors"], ref["feature_errors"] or "none")
        if a.expect_bodies is not None:
            check("bodies", ref["body_count"] == a.expect_bodies, "%s, expected %s" % (ref["body_count"], a.expect_bodies))
        if a.expect_volume is not None:
            check("volume", near(ref["volume_mm3"], a.expect_volume, a.tol),
                  "%s mm³, expected %s ±%s%%" % (ref["volume_mm3"], a.expect_volume, a.tol))
        if a.expect_size:
            check("size", all(abs(x - y) <= a.size_tol for x, y in zip(size, a.expect_size)),
                  "%s, expected %s" % (ref["overall_size"], a.expect_size))
    if a.inp:
        check("input unchanged", sha256(a.inp) == in_hash, a.inp)

    report["ok"] = all(c["ok"] for c in report["checks"])
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    print(text)
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
