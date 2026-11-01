#!/usr/bin/env python3
"""Build or edit a TextureCraft project from a JSON spec, checked before and after.

Spec (file path or inline JSON):
  {
    "in": "builtin:crate" | "mesh.glb" | "old.tcraft",   (or --in)
    "resolution": 2048,                                    (new projects only; default 2048)
    "steps": [
      {"id": "bake.run", "params": {"ts": "all", "maps": ["ambient_occlusion", "curvature"]}},
      {"sets": "all", "steps": [ {"id": "material.apply", "params": {"material": "iron_rusted"}} ]},
      {"sets": ["Lid"], "steps": [ {"id": "layer.add.fill", "params": {"name": "Paint", "color": [0.1, 0.3, 0.7]}} ]}
    ],
    "save": "out.tcraft"                                   (or --save)
  }

Before anything runs, every step is checked against `texturecraft-cli commands`: an unknown
id or a param key the command does not take stops the build (the CLI itself silently drops
unknown keys). A {"sets": …} group repeats its steps on each named texture set (names or
indices, or "all"), selecting the set first, since layer and mask commands act on the active
set only. A "ts" given as a set name is turned into its index. Generators (edge wear, dirt,
curvature…) and smart materials on a set with no baked mesh maps render as nothing, so that
is refused unless --allow-unbaked.

After the batch runs, the saved project is read back with `info`; --expect-layer SET:NAME and
--expect-baked SET:map,map check it. The input is never written; the output is refused if it
exists unless --overwrite. Prints JSON; exit 1 on any failed check.
"""
import argparse
import hashlib
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tclib  # noqa: E402

DEFAULT_MAPS = ["normal_base", "world_space_normals", "id", "ambient_occlusion", "curvature", "position", "thickness"]
GEN_NEEDS = {"edgeWear": "curvature", "curvature": "curvature", "dirt": "ambient_occlusion",
             "ambientOcclusion": "ambient_occlusion", "thinAreas": "thickness", "position": "position",
             "direction": "world_space_normals"}


def load_spec(arg):
    if os.path.exists(arg):
        with open(arg) as f:
            return json.load(f)
    return json.loads(arg)


def sha(path):
    if not os.path.isfile(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def set_index(sets, ref):
    if isinstance(ref, int):
        if 0 <= ref < len(sets):
            return ref
        raise tclib.TcError("no texture set %d (sets: %s)" % (ref, ", ".join(sets)))
    for i, n in enumerate(sets):
        if n == ref:
            return i
    for i, n in enumerate(sets):
        if n.lower() == str(ref).lower():
            return i
    raise tclib.TcError("no texture set named %r (sets: %s)" % (ref, ", ".join(sets)))


def expand(steps, sets):
    """Flatten {"sets": …} groups into textureSet.select + steps; map ts names to indices."""
    out = []
    for st in steps:
        if "sets" in st:
            refs = st["sets"]
            idx = list(range(len(sets))) if refs == "all" else [set_index(sets, r) for r in (refs if isinstance(refs, list) else [refs])]
            for i in idx:
                out.append({"id": "textureSet.select", "params": {"ts": i}})
                out.extend(expand(st.get("steps", []), sets))
            continue
        if "id" not in st:
            raise tclib.TcError("step without id: %s" % json.dumps(st))
        params = dict(st.get("params") or {})
        ts = params.get("ts")
        if isinstance(ts, str) and ts not in ("all", "selected"):
            params["ts"] = set_index(sets, ts)
        elif isinstance(ts, list):
            params["ts"] = [set_index(sets, t) for t in ts]
        out.append({"id": st["id"], "params": params})
    return out


def check_bakes(steps, sets, baked, active):
    """Walk the steps, tracking the active set and what is baked; list generator steps on unbaked sets."""
    problems = []
    pending_maps = {}
    for n, st in enumerate(steps):
        cid, p = st["id"], st["params"]
        if cid == "textureSet.select":
            active = p.get("ts", active)
        elif cid == "bake.settings" and "maps" in p:
            for i in _ts_targets(p.get("ts"), active, len(sets)):
                pending_maps[i] = list(p["maps"])
        elif cid == "bake.run":
            for i in _ts_targets(p.get("ts"), active, len(sets)):
                maps = p.get("maps") or pending_maps.get(i) or DEFAULT_MAPS
                baked[i] = set(baked.get(i, set())) | set(maps)
        elif cid == "effect.add.generator":
            need = GEN_NEEDS.get(p.get("generator", "edgeWear"))
            if need and need not in baked.get(active, set()):
                problems.append("step %d: %s generator on set %r, which has no baked %s" % (n, p.get("generator", "edgeWear"), sets[active], need))
        elif cid in ("material.apply", "material.load", "mask.smart.apply"):
            if not baked.get(active):
                problems.append("step %d: %s on set %r, which has no baked mesh maps (its generators would render empty)" % (n, cid, sets[active]))
    return problems


def _ts_targets(ts, active, n):
    if ts in (None, "selected"):
        return [active]
    if ts == "all":
        return list(range(n))
    if isinstance(ts, list):
        return ts
    return [ts]


def layer_names(layers):
    out = []
    for l in layers or []:
        out.append(l.get("name"))
        out.extend(layer_names(l.get("children")))
    return out


def summarise(path):
    d = tclib.info(path)
    sets = []
    for t in d["textureSets"]:
        layers = tclib.command(path, "layer.list", {"ts": t["index"]})
        sets.append({"index": t["index"], "name": t["name"], "resolution": t["resolution"],
                     "baked": t["baked"], "layers": [_tree(l) for l in layers]})
    return d, sets


def _tree(l):
    node = {"id": l["id"], "name": l["name"], "kind": l["kind"]}
    if l.get("mask"):
        node["mask"] = [e.get("name") or e.get("kind") for e in l["mask"].get("effects", [])] or l["mask"].get("background")
    if l.get("children"):
        node["children"] = [_tree(c) for c in l["children"]]
    return node


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", help="spec JSON file or inline JSON")
    ap.add_argument("--in", dest="inp", help="input: builtin:<id>, a mesh file or a .tcraft (overrides spec.in)")
    ap.add_argument("--save", help="output .tcraft (overrides spec.save)")
    ap.add_argument("--resolution", type=int, help="texture size for a new project (overrides spec.resolution)")
    ap.add_argument("--expect-layer", action="append", default=[], metavar="SET:NAME",
                    help="a layer whose name contains NAME exists in SET (name, index or 'all')")
    ap.add_argument("--expect-baked", action="append", default=[], metavar="SET:MAP,MAP",
                    help="SET (or 'all') has these mesh maps baked")
    ap.add_argument("--allow-unbaked", action="store_true", help="run generators / smart materials on unbaked sets anyway")
    ap.add_argument("--dry-run", action="store_true", help="check and print the expanded batch; run nothing")
    ap.add_argument("--overwrite", action="store_true", help="replace an existing output")
    a = ap.parse_args()

    spec = load_spec(a.spec)
    inp = a.inp or spec.get("in")
    out = a.save or spec.get("save")
    if not inp or not out:
        raise tclib.TcError("need an input (--in or spec.in) and an output (--save or spec.save)")
    if not out.endswith(".tcraft"):
        raise tclib.TcError("output must be a .tcraft project: %s" % out)
    if not inp.startswith("builtin:") and not os.path.exists(inp):
        raise tclib.TcError("input not found: %s" % inp)
    if not inp.startswith("builtin:") and tclib.same_file(inp, out):
        raise tclib.TcError("refusing to save over the input; pick a new output path")
    tclib.refuse_overwrite(out, a.overwrite)
    before = sha(inp) if not inp.startswith("builtin:") else None

    tmpdir = tempfile.mkdtemp(prefix="tc_build_")
    try:
        if inp.endswith(".tcraft"):
            base = inp
        else:
            base = os.path.join(tmpdir, "new.tcraft")
            res = a.resolution or spec.get("resolution") or 2048
            tclib.run(["new", inp, base, "--resolution", str(res)])
        d = tclib.info(base)
        sets = [t["name"] for t in d["textureSets"]]
        baked = {t["index"]: set((t.get("baked") or {}).get("maps", [])) for t in d["textureSets"]}
        steps = expand(spec.get("steps", []), sets)

        problems = []
        for n, st in enumerate(steps):
            problems += ["step %d: %s" % (n, p) for p in tclib.check_step(st["id"], st["params"])]
        bake_problems = check_bakes(steps, sets, baked, d.get("activeTextureSet", 0))
        if not a.allow_unbaked:
            problems += bake_problems
        if problems or a.dry_run:
            tclib.emit({"ok": not problems, "dry_run": a.dry_run, "sets": sets, "problems": problems,
                        "warnings": bake_problems if a.allow_unbaked else [], "steps": steps}, ok=not problems)

        script = os.path.join(tmpdir, "batch.json")
        with open(script, "w") as f:
            json.dump({"open": os.path.abspath(base), "steps": steps, "save": os.path.abspath(out)}, f)
        result = tclib.run_json(["batch", script])
        if result and result.get("failed"):
            tclib.emit({"ok": False, "error": "batch failed", "result": result, "steps": steps}, ok=False)
        if not os.path.exists(out):
            raise tclib.TcError("batch reported success but %s was not written" % out)

        info, sets_out = summarise(out)
        checks = []
        for e in a.expect_layer:
            sref, name = e.split(":", 1)
            for s in _pick(sets_out, sref):
                names = layer_names(tclib.command(out, "layer.list", {"ts": s["index"]}))
                ok = any(name.lower() in (n or "").lower() for n in names)
                checks.append({"check": "layer %r in %s" % (name, s["name"]), "ok": ok})
        for e in a.expect_baked:
            sref, maps = e.split(":", 1)
            for s in _pick(sets_out, sref):
                have = set((s["baked"] or {}).get("maps", []))
                miss = [m for m in maps.split(",") if m and m not in have]
                checks.append({"check": "baked %s in %s" % (maps, s["name"]), "ok": not miss, "missing": miss})
        if before is not None:
            checks.append({"check": "input unchanged", "ok": sha(inp) == before})
        ok = all(c["ok"] for c in checks)
        tclib.emit({"ok": ok, "saved": out, "version": tclib.version(), "steps": len(steps),
                    "results": result.get("results") if result else None,
                    "warnings": bake_problems if a.allow_unbaked else [],
                    "mesh": info.get("mesh"), "textureSets": sets_out, "checks": checks}, ok=ok)
    finally:
        for fn in os.listdir(tmpdir):
            os.remove(os.path.join(tmpdir, fn))
        os.rmdir(tmpdir)


def _pick(sets_out, ref):
    if ref == "all":
        return sets_out
    return [s for s in sets_out if s["name"].lower() == ref.lower() or str(s["index"]) == ref]


if __name__ == "__main__":
    tclib.main_guard(main)
