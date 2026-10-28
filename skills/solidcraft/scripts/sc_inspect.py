#!/usr/bin/env python3
"""Measure a part (STEP, STL, 3MF, OBJ, .solidcraft) and render snapshots of it.

  sc_inspect.py part.step
  sc_inspect.py part.step --snap-dir shots --views iso top --section mid
  sc_inspect.py part.step --snap-dir shots --section z=12.5 --section XZ --json-out part.json

Prints JSON: body count, total volume (mm³) and mass, the overall bounding box (min,
max, size), and per body its name, closed flag, volume, size and face types. The file is
only read; its hash is checked before and after.

Snapshots (`solidcraft-cli snapshot`, headless) go to --snap-dir as NAME-VIEW.png and
NAME-section-SPEC.png. --section takes what `snapshot --section` takes (z=27, z=27,flip,
XY, XZ, YZ) or `mid` for the plane through the middle of the bounding box in Z. Each
section is rendered in --section-view (default iso) and compared against a plain render
of the same view, so a section that cut nothing fails. Every PNG is checked to be a real,
non-blank image. Exits 1 on any failed check.
"""
import argparse
import json
import os
import re
import sys

from sclib import evaluate, png_diff, png_stats, refuse_existing, run_cli, sha256, summary


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("part")
    ap.add_argument("--snap-dir")
    ap.add_argument("--views", nargs="*", default=None,
                    help="iso front back top bottom left right, or a saved view name (default: iso)")
    ap.add_argument("--section", action="append", default=[])
    ap.add_argument("--section-view", default="iso")
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=800)
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--json-out")
    a = ap.parse_args()

    h0 = sha256(a.part)
    sm = summary(evaluate(a.part))
    bodies = sm["bodies"]
    lo = [min(b["bbox_min"][i] for b in bodies) for i in range(3)] if bodies else None
    hi = [max(b["bbox_max"][i] for b in bodies) for i in range(3)] if bodies else None
    report = {
        "file": a.part,
        "body_count": sm["body_count"],
        "volume_mm3": sm["volume_mm3"], "mass_g": sm["mass_g"],
        "open_bodies_skipped": sm["open_bodies_skipped"],
        "bbox": lo and {"min": lo, "max": hi, "size": [round(h - l, 3) for l, h in zip(lo, hi)]},
        "bodies": [{k: b[k] for k in ("name", "closed", "volume_mm3", "size", "face_types")} for b in bodies],
        "snapshots": [], "checks": [],
    }

    def check(name, ok, detail):
        report["checks"].append({"check": name, "ok": bool(ok), "detail": detail})

    if a.snap_dir or a.section or a.views:
        if not a.snap_dir:
            ap.error("snapshots need --snap-dir")
        os.makedirs(a.snap_dir, exist_ok=True)
        stem = os.path.splitext(os.path.basename(a.part))[0]
        views = a.views if a.views is not None else ["iso"]
        jobs = [(os.path.join(a.snap_dir, "%s-%s.png" % (stem, v)), v, None) for v in views]
        for spec in a.section:
            if spec == "mid":
                if not lo:
                    sys.exit("no bodies to cut")
                spec = "z=%g" % round((lo[2] + hi[2]) / 2, 3)
            tag = re.sub(r"[^A-Za-z0-9.=-]+", "_", spec).replace("=", "")
            jobs.append((os.path.join(a.snap_dir, "%s-section-%s.png" % (stem, tag)), a.section_view, spec))
        plain = {v: p for p, v, sec in jobs if sec is None}
        need_ref = {v for _, v, sec in jobs if sec is not None and v not in plain}
        for v in need_ref:
            plain[v] = os.path.join(a.snap_dir, "%s-%s.png" % (stem, v))
            jobs.insert(0, (plain[v], v, None))
        refuse_existing([p for p, _, _ in jobs], a.overwrite)
        for path, view, sec in jobs:
            args = ["snapshot", "--in", a.part, "--out", path, "--width", str(a.width), "--height", str(a.height),
                    "--view", view]
            if sec:
                args += ["--section", sec]
            run_cli(args)
            st = png_stats(path)
            report["snapshots"].append({"path": path, "view": view, "section": sec, **st})
            check("image " + path, (st["width"], st["height"]) == (a.width, a.height) and st["colours"] > 8
                  and st["content_share"] > 0.01, st)
            if sec:
                d = png_diff(path, plain[view])
                check("section differs from plain " + view, d > 0.5, "mean difference %s" % d)

    check("input unchanged", sha256(a.part) == h0, a.part)
    report["ok"] = all(c["ok"] for c in report["checks"])
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    print(text)
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
