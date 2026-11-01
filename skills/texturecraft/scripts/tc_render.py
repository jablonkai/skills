#!/usr/bin/env python3
"""Render a project (or mesh) to PNG for visual checks, and make sure the image is not blank.

  tc_render.py crate.tcraft crate.png                       # 3D viewport, default camera
  tc_render.py crate.tcraft crate.png --yaw 215 --pitch 20  # the other side
  tc_render.py crate.tcraft crate.png --uv                  # also crate-uv.png: the 2D (UV) view
  tc_render.py crate.tcraft hero.png --samples 128          # path traced
  tc_render.py crate.tcraft crate.png --cpu --samples 16    # no GPU adapter

The viewport render needs a GPU or a software adapter. If it fails and --cpu was not given,
the render is retried once on the CPU path tracer (16 samples unless --samples) and the
result says so. Each PNG is checked to exist, have the asked size and show more than a flat
background. Read the PNGs afterwards: only the picture shows a mask on the wrong set.
Prints JSON; exit 1 on any failed check.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tclib  # noqa: E402


def render(inp, out, a, view, cpu=False, samples=None):
    args = ["render", inp, out, "--size", a.size, "--view", view]
    if a.yaw is not None:
        args += ["--yaw", str(a.yaw)]
    if a.pitch is not None:
        args += ["--pitch", str(a.pitch)]
    if samples:
        args += ["--samples", str(samples)]
        if a.bounces:
            args += ["--bounces", str(a.bounces)]
    if cpu:
        args.append("--cpu")
    lines = tclib.run(args, stderr=True).strip().splitlines()  # "wrote X (WxH, adapter, s)" is on stderr
    return lines[-1] if lines else ""


def check(path, size):
    w, h = [int(x) for x in size.lower().split("x")]
    if not os.path.exists(path):
        return {"file": path, "ok": False, "error": "not written"}
    st = tclib.png_stats(path)
    lively = st["distinct"] > 64 and max(st["std"][:3]) > 4
    ok = st["width"] == w and st["height"] == h and lively
    return {"file": path, "ok": ok, "width": st["width"], "height": st["height"],
            "distinct_colours": st["distinct"], "std": st["std"],
            "error": None if ok else ("wrong size" if st["width"] != w or st["height"] != h else "looks blank")}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help=".tcraft project, mesh file or builtin:<id>")
    ap.add_argument("out", help="output .png")
    ap.add_argument("--size", default="1024x1024", help="WxH (default 1024x1024)")
    ap.add_argument("--view", choices=["3d", "2d"], default="3d")
    ap.add_argument("--uv", action="store_true", help="also render the 2D (UV) view to <out>-uv.png")
    ap.add_argument("--yaw", type=float)
    ap.add_argument("--pitch", type=float)
    ap.add_argument("--samples", type=int, help="path trace with N samples instead of the viewport")
    ap.add_argument("--bounces", type=int)
    ap.add_argument("--cpu", action="store_true", help="CPU path tracer (implies --samples 16 unless given)")
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args()

    if not a.out.lower().endswith(".png"):
        raise tclib.TcError("output must be .png")
    if not a.input.startswith("builtin:") and not os.path.exists(a.input):
        raise tclib.TcError("not found: %s" % a.input)
    jobs = [(a.out, a.view)]
    if a.uv:
        jobs.append((a.out[:-4] + "-uv.png", "2d"))
    for path, _ in jobs:
        tclib.refuse_overwrite(path, a.overwrite)
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    results, ok = [], True
    for path, view in jobs:
        samples = a.samples or (16 if a.cpu else None)
        note = None
        try:
            line = render(a.input, path, a, view, cpu=a.cpu, samples=samples)
        except tclib.TcError as e:
            if a.cpu:
                raise
            note = "viewport render failed (%s); retried on the CPU path tracer" % e
            line = render(a.input, path, a, view, cpu=True, samples=a.samples or 16)
        r = check(path, a.size)
        r.update(view=view, renderer=line, note=note)
        ok = ok and r["ok"]
        results.append(r)
    tclib.emit({"ok": ok, "renders": results}, ok=ok)


if __name__ == "__main__":
    tclib.main_guard(main)
