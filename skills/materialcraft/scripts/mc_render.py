#!/usr/bin/env python3
"""Render a MaterialCraft material for a look, a variant sweep or a tiling check.

  mc_render.py IN OUT.png [--view 3d|2d] [--scene sphere] [--node ID] [--size WxH]
               [--yaw D] [--pitch D] [--graph N] [--set ID=VALUE]... [--tiling N] [--hq [--displacement R]]
  mc_render.py IN OUT.png --variants wear=0,0.5,1 [...]   # OUT_wear-0.png, OUT_wear-0.5.png, ...
  mc_render.py IN OUT.png --tile 3 [--node ID]             # 3x3 repeat of one map (2D), assembled here
  mc_render.py IN --seam [NODE ...]                        # wrap-around seam score per output or node

A 3D render that comes out flat (one colour) fails; a 2D one only warns, since a uniform map is
legitimate. Variant renders must differ from each other, or the input is not wired to anything
visible. --tile N renders the node (default: the base colour output) in 2D at the graph size and
repeats it N x N itself: the CLI's `--view 2d --tiling N` is ignored in 0.1.0 (3D --tiling works,
it repeats the UVs). --seam renders each output (or the given node ids) in 2D at the graph's own size and
scores the wrap-around edges: up to 1.5 tiles, above it the wrap is a visible seam.
Prints JSON; exits 1 on any failed check.
"""
import argparse
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mclib as m  # noqa: E402


def render(inp, out, a, extra_sets=None):
    args = ["render", inp, out]
    for flag in ("view", "scene", "node", "size", "yaw", "pitch", "graph", "tiling", "displacement"):
        v = getattr(a, flag, None)
        if v is not None:
            args += ["--" + flag, str(v)]
    if getattr(a, "hq", False):
        args.append("--hq")
    sets = dict(a.sets)
    sets.update(extra_sets or {})
    for k, v in sets.items():
        args += ["--set", "%s=%s" % (k, json.dumps(v))]
    return m.run_json(args)


def parse_value(v):
    try:
        return json.loads(v)
    except ValueError:
        return v


def diff(a, b):
    _, _, _, ra = m.png_pixels(a, 128)
    _, _, _, rb = m.png_pixels(b, 128)
    tot = n = 0
    for r1, r2 in zip(ra, rb):
        for p, q in zip(r1, r2):
            tot += sum(abs(x - y) for x, y in zip(p[:3], q[:3]))
            n += 3
    return round(tot / n, 2) if n else 0.0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inp")
    ap.add_argument("out", nargs="?", help="output PNG (stem for --variants)")
    ap.add_argument("--view", choices=["3d", "2d"])
    ap.add_argument("--scene", choices=["rounded_cube", "cube", "sphere", "cylinder", "plane", "torus", "material_ball"])
    ap.add_argument("--node", type=int, help="node id for --view 2d (default: the base colour output)")
    ap.add_argument("--size", help="WxH")
    ap.add_argument("--yaw", type=float)
    ap.add_argument("--pitch", type=float)
    ap.add_argument("--graph", type=int)
    ap.add_argument("--tiling", type=int)
    ap.add_argument("--hq", action="store_true", help="beauty render: displacement, AO, key light (slower)")
    ap.add_argument("--displacement", type=float)
    ap.add_argument("--set", action="append", default=[], metavar="ID=VALUE")
    ap.add_argument("--tile", type=int, metavar="N", help="write an N x N 2D repeat of one node's map")
    ap.add_argument("--variants", metavar="ID=V1,V2,...", help="one render per value of one exposed input")
    ap.add_argument("--seam", nargs="*", type=int, metavar="NODE", help="tiling check (no ids: every output)")
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args()
    a.sets = {}
    for s in a.set:
        k, _, v = s.partition("=")
        a.sets[k] = parse_value(v)

    g = m.graph_of(a.inp, a.graph)
    exposed = {e["id"] for e in g.get("exposed", [])}
    bad = [k for k in a.sets if k not in exposed]
    if a.variants:
        bad += [k for k in [a.variants.partition("=")[0]] if k not in exposed]
    if bad:
        m.emit({"ok": False, "error": "no exposed input %s (has %s)" % (bad, sorted(exposed))}, ok=False)

    if a.seam is not None:
        targets = a.seam or [o["node"] for o in m.outputs(g)]
        names = {o["node"]: o["identifier"] for o in m.outputs(g)}
        tmp = tempfile.mkdtemp(prefix="mc-seam-")
        res, fails = [], []
        for nid in targets:
            p = os.path.join(tmp, "n%d.png" % nid)
            ns = argparse.Namespace(view="2d", node=nid, size="%dx%d" % tuple(g["size"]), graph=a.graph, sets=a.sets)
            render(a.inp, p, ns)
            s = m.seam(p)
            s.update({"node": nid, "output": names.get(nid)})
            res.append(s)
            if not s["tiles"]:
                fails.append("node %d%s: seam x=%s y=%s" % (nid, " (%s)" % names[nid] if nid in names else "",
                                                           s["x"], s["y"]))
        m.emit({"ok": not fails, "graph": g["name"], "size": g["size"], "seam": res, "failed": fails}, ok=not fails)

    if not a.out:
        ap.error("OUT.png is required unless --seam")
    if a.tile:
        if a.node is None:
            base = [o["node"] for o in m.outputs(g) if o["usage"] == "Base color"]
            a.node = base[0] if base else None
        if a.node is None:
            m.emit({"ok": False, "error": "no base colour output; pass --node"}, ok=False)
        m.refuse_overwrite(a.out, a.overwrite, "render")
        one = os.path.join(tempfile.mkdtemp(prefix="mc-tile-"), "one.png")
        ns = argparse.Namespace(view="2d", node=a.node, size="%dx%d" % tuple(g["size"]), graph=a.graph, sets=a.sets)
        render(a.inp, one, ns)
        size = m.tile_png(one, a.out, a.tile)
        s = m.seam(one)
        m.emit({"ok": True, "file": a.out, "node": a.node, "tiles": a.tile, "size": [size["width"], size["height"]],
                "seam": {"x": s["x"], "y": s["y"]}, "seamless": s["tiles"]})
    if a.view == "2d" and a.node is None:
        base = [o["node"] for o in m.outputs(g) if o["usage"] == "Base color"]
        if base:
            a.node = base[0]
    flat_fails = a.view != "2d"

    jobs = []
    if a.variants:
        key, _, vals = a.variants.partition("=")
        stem, ext = os.path.splitext(a.out)
        for v in vals.split(","):
            jobs.append(("%s_%s-%s%s" % (stem, key, v.strip().lstrip("#"), ext or ".png"), {key: parse_value(v.strip())}))
    else:
        jobs.append((a.out, {}))
    for path, _ in jobs:
        m.refuse_overwrite(path, a.overwrite, "render")

    res, fails, warns = [], [], []
    for path, extra in jobs:
        r = render(a.inp, path, a, extra)
        st = m.png_stats(path)
        row = {"file": path, "size": [r.get("width"), r.get("height")], "set": dict(a.sets, **extra),
               "mean": st["mean"][:3], "distinct": st["distinct"]}
        if st["distinct"] <= 1:
            (fails if flat_fails else warns).append("%s is a single flat colour" % path)
        res.append(row)
    if len(res) > 1:
        for i in range(len(res)):
            for j in range(i + 1, len(res)):
                d = diff(res[i]["file"], res[j]["file"])
                if d < 0.5:
                    fails.append("%s and %s look the same (mean diff %s)" % (res[i]["file"], res[j]["file"], d))
    m.emit({"ok": not fails, "renders": res, "warnings": warns, "failed": fails}, ok=not fails)


if __name__ == "__main__":
    m.main_guard(main)
