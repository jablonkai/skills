#!/usr/bin/env python3
"""Check SolidCraft outputs against expected values; print JSON, exit 1 on any failure.

  sc_verify.py part F [--bodies N] [--volume V] [--tol PCT] [--size X Y Z] [--size-tol MM]
                      [--param NAME=EXPR]… [--params-exact NAME…] [--no-errors] [--closed]
                      [--face-type cylinder=8]… [--same-as OTHER [--same-tol PCT]]
  sc_verify.py png F [--width W] [--height H] [--not-blank] [--differs OTHER.png]
  sc_verify.py hash PATH… --save m.json | --compare m.json

`part` reads any file `solidcraft-cli eval` opens (.solidcraft, STEP, STL, 3MF, OBJ) or a
command script. --size is the overall bounding box; --params-exact fails when the design
has any user parameter not named (a misspelled `parameters.change` adds one);
--same-as compares volume and size with another file (an export against its design).
With no checks, `part` prints the summary.
"""
import argparse
import json
import os
import sys

from sclib import evaluate, png_diff, png_stats, sha256, summary


def overall(sm):
    b = sm["bodies"]
    if not b:
        return [0.0, 0.0, 0.0]
    return [round(max(x["bbox_max"][i] for x in b) - min(x["bbox_min"][i] for x in b), 4) for i in range(3)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("part")
    p.add_argument("file")
    p.add_argument("--bodies", type=int)
    p.add_argument("--volume", type=float)
    p.add_argument("--tol", type=float, default=0.5, help="volume tolerance %% (default 0.5)")
    p.add_argument("--size", type=float, nargs=3)
    p.add_argument("--size-tol", type=float, default=0.01)
    p.add_argument("--param", action="append", default=[])
    p.add_argument("--params-exact", nargs="*", action="extend")
    p.add_argument("--no-errors", action="store_true")
    p.add_argument("--closed", action="store_true", help="every body is a closed solid")
    p.add_argument("--face-type", action="append", default=[], help="TYPE=N total over all bodies")
    p.add_argument("--same-as")
    p.add_argument("--same-tol", type=float, default=0.1)
    g = sub.add_parser("png")
    g.add_argument("file")
    g.add_argument("--width", type=int)
    g.add_argument("--height", type=int)
    g.add_argument("--not-blank", action="store_true")
    g.add_argument("--differs")
    h = sub.add_parser("hash")
    h.add_argument("paths", nargs="+")
    h.add_argument("--save")
    h.add_argument("--compare")
    a = ap.parse_args()

    checks = []

    def check(name, ok, detail):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    out = {}
    if a.mode == "part":
        sm = summary(evaluate(a.file))
        size = overall(sm)
        out = {"file": a.file, "body_count": sm["body_count"], "volume_mm3": sm["volume_mm3"],
               "size": size, "params": sm["params"], "features": sm["features"]}
        if a.bodies is not None:
            check("bodies", sm["body_count"] == a.bodies, "%s, expected %s" % (sm["body_count"], a.bodies))
        if a.volume is not None:
            v = sm["volume_mm3"]
            check("volume", v is not None and abs(v - a.volume) <= abs(a.volume) * a.tol / 100,
                  "%s, expected %s ±%s%%" % (v, a.volume, a.tol))
        if a.size:
            check("size", all(abs(x - y) <= a.size_tol for x, y in zip(size, a.size)),
                  "%s, expected %s" % (size, a.size))
        for item in a.param:
            name, expr = item.split("=", 1)
            got = sm["params"].get(name)
            check("param " + name, got is not None and got.replace(" ", "") == expr.replace(" ", ""),
                  "%r, expected %r" % (got, expr))
        if a.params_exact is not None:
            extra = sorted(set(sm["params"]) - set(a.params_exact))
            missing = sorted(set(a.params_exact) - set(sm["params"]))
            check("params exactly %s" % a.params_exact, not extra and not missing,
                  {"extra": extra, "missing": missing})
        if a.no_errors:
            check("no feature errors", not sm["feature_errors"], sm["feature_errors"] or "none")
        if a.closed:
            open_ = [b["name"] for b in sm["bodies"] if not b["closed"]]
            check("closed bodies", not open_ and sm["bodies"], open_ or "all closed")
        for item in a.face_type:
            t, n = item.split("=", 1)
            got = sum((b.get("face_types") or {}).get(t, 0) for b in sm["bodies"])
            check("%s faces" % t, got == int(n), "%s, expected %s" % (got, n))
        if a.same_as:
            o = summary(evaluate(a.same_as))
            ov, v = o["volume_mm3"], sm["volume_mm3"]
            check("volume same as " + a.same_as, ov and v and abs(v - ov) <= ov * a.same_tol / 100,
                  "%s vs %s (±%s%%)" % (v, ov, a.same_tol))
            os_ = overall(o)
            check("size same as " + a.same_as, all(abs(x - y) <= 0.05 for x, y in zip(size, os_)),
                  "%s vs %s" % (size, os_))
    elif a.mode == "png":
        st = png_stats(a.file)
        out = {"file": a.file, **st}
        if a.width:
            check("width", st["width"] == a.width, st["width"])
        if a.height:
            check("height", st["height"] == a.height, st["height"])
        if a.not_blank:
            check("not blank", st["colours"] > 8 and st["content_share"] > 0.01, st)
        if a.differs:
            d = png_diff(a.file, a.differs)
            check("differs from " + a.differs, d > 0.5, "mean difference %s" % d)
    else:
        hashes = {os.path.abspath(p): sha256(p) for p in a.paths}
        out = {"hashes": hashes}
        if a.save:
            with open(a.save, "w", encoding="utf-8") as f:
                json.dump(hashes, f, indent=2)
        if a.compare:
            with open(a.compare, encoding="utf-8") as f:
                old = json.load(f)
            for path, hv in old.items():
                check("unchanged " + path, hashes.get(path, sha256(path) if os.path.exists(path) else None) == hv,
                      path)

    out["checks"] = checks
    out["ok"] = all(c["ok"] for c in checks)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    sys.exit(0 if out["ok"] else 1)


if __name__ == "__main__":
    main()
