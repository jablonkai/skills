#!/usr/bin/env python3
"""Export a project's textures (and optionally the textured mesh), then check every file.

  tc_export.py crate.tcraft out/ --preset "glTF PBR Metal Roughness"
  tc_export.py model.tcraft out/ --preset "glTF PBR Metal Roughness" --size 1024 --normal directx
  tc_export.py model.tcraft out/ --preset "Unreal Engine (Packed)" --ts Body --format tga
  tc_export.py model.tcraft out/ --preset my-preset.json            # a preset object {name, maps}
  tc_export.py model.tcraft out/ --preset "glTF PBR Metal Roughness" --mesh out/model.glb
  tc_export.py model.tcraft out/ --plan-only                        # list what would be written

Runs `export.plan` first, then `file.exportTextures` (the `export` subcommand has no way to
pick a texture set or the normal convention), and checks:
  * the written files are exactly the planned ones;
  * each file decodes with the expected width/height (--size, else the set's resolution);
  * with --normal directx|opengl, the green channel of each normal map is the inverse of
    the opposite convention's export (a flat normal map cannot show the difference and is
    reported as such);
  * with --mesh, the mesh file re-imports with `info`, has the project's triangle count and,
    for .glb, an embedded image and texture link for every material.
The project is never written. A non-empty output folder is refused unless --overwrite.
Prints JSON; exit 1 on any failed check.
"""
import argparse
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tclib  # noqa: E402

NORMAL = {"directx": "directX", "opengl": "openGl"}


def resolve_ts(inp, ts):
    if ts in (None, "all"):
        return ts
    if ts.isdigit():
        return int(ts)
    sets = [t["name"] for t in tclib.info(inp)["textureSets"]]
    for i, n in enumerate(sets):
        if n.lower() == ts.lower():
            return i
    raise tclib.TcError("no texture set %r (sets: %s)" % (ts, ", ".join(sets)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", help=".tcraft project (a mesh file or builtin:<id> works too, untextured)")
    ap.add_argument("dir", help="output folder")
    ap.add_argument("--preset", help="built-in or user preset name, or a JSON file holding a preset object {name, maps}")
    ap.add_argument("--ts", help="one texture set (name or index); default all")
    ap.add_argument("--format", help="png, jpg, tga, tif, exr … (overrides the preset)")
    ap.add_argument("--bit-depth", type=int, help="8, 16 or 32 (overrides the preset)")
    ap.add_argument("--size", type=int, help="output size in px (power of two); default each set's resolution")
    ap.add_argument("--padding", choices=["none", "dilation", "dilationDefault", "infinite"])
    ap.add_argument("--dilation", type=int, help="dilation width in px")
    ap.add_argument("--normal", choices=["directx", "opengl"], help="normal map convention, checked on the output")
    ap.add_argument("--mesh", help="also export the textured mesh here (.glb .obj .usda .usdc .usdz) and re-import it")
    ap.add_argument("--plan-only", action="store_true", help="print export.plan; write nothing")
    ap.add_argument("--overwrite", action="store_true", help="allow a non-empty output folder / existing mesh file")
    a = ap.parse_args()

    if not a.project.startswith("builtin:") and not os.path.exists(a.project):
        raise tclib.TcError("not found: %s" % a.project)
    preset = None
    if a.preset:
        preset = a.preset
        if a.preset.endswith(".json") and os.path.exists(a.preset):
            with open(a.preset) as f:
                preset = json.load(f)
    ts = resolve_ts(a.project, a.ts)

    plan_params = {k: v for k, v in (("preset", preset), ("ts", ts), ("format", a.format),
                                      ("bitDepth", a.bit_depth), ("size", a.size)) if v is not None}
    try:
        plan = tclib.command(a.project, "export.plan", plan_params)
    except tclib.TcError as e:
        if "unknown export preset" not in str(e):
            raise
        names = [p["name"] for p in tclib.command(a.project, "export.presets")]
        word = str(preset).split()[0].lower()
        close = [n for n in names if word in n.lower()]
        raise tclib.TcError("%s; did you mean %s? presets: %s" % (e, " or ".join(repr(n) for n in close) or "-", "; ".join(names)))
    warnings = [w for p in plan for w in p.get("warnings", [])]
    if a.plan_only:
        tclib.emit({"ok": True, "plan": plan, "warnings": warnings})
    if not plan:
        raise tclib.TcError("export.plan lists no outputs (preset maps the project lacks?)")

    if os.path.isdir(a.dir) and os.listdir(a.dir) and not a.overwrite:
        raise tclib.TcError("output folder %s is not empty; pass --overwrite or pick a new folder" % a.dir)
    if a.mesh:
        tclib.refuse_overwrite(a.mesh, a.overwrite, "mesh")
    os.makedirs(a.dir, exist_ok=True)

    params = dict(plan_params, dir=a.dir)
    for k, v in (("padding", a.padding), ("dilation", a.dilation)):
        if v is not None:
            params[k] = v
    if a.normal:
        params["normalFormat"] = NORMAL[a.normal]
    result = tclib.command(a.project, "file.exportTextures", params)
    written = [os.path.basename(f) for f in result.get("files", [])]
    warnings += result.get("warnings", [])

    d = tclib.info(a.project) if not a.project.startswith("builtin:") else None
    res_by_ts = {t["index"]: t["resolution"] for t in d["textureSets"]} if d else {}
    planned = [p["file"] for p in plan]
    checks = [{"check": "written files == export.plan", "ok": sorted(written) == sorted(planned),
               "missing": sorted(set(planned) - set(written)), "extra": sorted(set(written) - set(planned))}]
    files = []
    for p in plan:
        path = os.path.join(a.dir, p["file"])
        entry = {"file": p["file"], "ts": p["ts"]}
        if not os.path.exists(path):
            entry["ok"] = False
            entry["error"] = "missing"
        else:
            hdr = tclib.image_header(path)
            want = a.size or res_by_ts.get(p["ts"])
            entry.update({k: hdr[k] for k in ("format", "width", "height", "channels", "bit_depth")})
            entry["ok"] = want is None or (hdr["width"] == want and hdr["height"] == want)
            if not entry["ok"]:
                entry["error"] = "expected %dx%d" % (want, want)
        files.append(entry)
    checks.append({"check": "every file decodes at the expected size", "ok": all(f["ok"] for f in files)})

    if a.normal:
        checks.append(check_normals(a, preset, ts, plan))
    if a.mesh:
        checks.extend(export_mesh(a, d))

    ok = all(c["ok"] for c in checks)
    tclib.emit({"ok": ok, "dir": a.dir, "version": tclib.version(), "files": files,
                "warnings": warnings, "checks": checks}, ok=ok)


def check_normals(a, preset, ts, plan):
    """Export the opposite convention to a temp folder and compare the green channels."""
    normals = [p["file"] for p in plan if "normal" in p["file"].lower() and p["format"] == "png"
               and "world" not in p["file"].lower() and "base" not in p["file"].lower()]
    if not normals:
        return {"check": "normal convention %s" % a.normal, "ok": True, "note": "no PNG normal map in this export"}
    other = "opengl" if a.normal == "directx" else "directx"
    tmp = tempfile.mkdtemp(prefix="tc_normal_")
    try:
        # same size as the real export: resampled noise would not line up pixel for pixel
        params = {k: v for k, v in (("preset", preset), ("ts", ts), ("size", a.size)) if v is not None}
        params.update(dir=tmp, normalFormat=NORMAL[other], format="png", bitDepth=8)
        tclib.command(a.project, "file.exportTextures", params)
        per = []
        for name in normals:
            mine = tclib.png_pixels(os.path.join(a.dir, name), max_side=256)
            ref = tclib.png_pixels(os.path.join(tmp, name), max_side=256)
            g1 = [p[1] for r in mine[3] for p in r]
            g2 = [p[1] for r in ref[3] for p in r]
            if len(g1) != len(g2):  # different export sizes: compare after resampling the index
                step = len(g1) / float(len(g2))
                g1 = [g1[int(i * step)] for i in range(len(g2))]
            flat = max(g2) - min(g2) <= 4
            inv = sum(abs(x + y - 255) for x, y in zip(g1, g2)) / len(g2)
            per.append({"file": name, "flat": flat, "green_inverse_error": round(inv, 2)})
        bent = [p for p in per if not p["flat"]]
        ok = all(p["green_inverse_error"] < 6 for p in bent)
        note = None if bent else "every normal map is flat, so the convention cannot be seen in the pixels"
        return {"check": "normal maps are %s (green inverted vs %s)" % (a.normal, other), "ok": ok,
                "maps": per, "note": note}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def export_mesh(a, d):
    checks = []
    tclib.command(a.project, "file.exportMesh", {"path": a.mesh})
    if not os.path.exists(a.mesh):
        return [{"check": "mesh written", "ok": False}]
    back = tclib.info(a.mesh)
    want = (d or {}).get("mesh", {}).get("triangles")
    checks.append({"check": "mesh re-imports with the project's triangle count", "ok": want is None or back.get("triangles") == want,
                   "triangles": back.get("triangles"), "expected": want, "textureSets": back.get("textureSets")})
    if a.mesh.lower().endswith(".glb"):
        g = tclib.glb_summary(a.mesh)
        textured = all(m["baseColorTexture"] for m in g["materials"])
        checks.append({"check": "glb embeds textures for every material", "ok": g["images"] > 0 and textured,
                       "images": g["images"], "materials": g["materials"]})
    return checks


if __name__ == "__main__":
    tclib.main_guard(main)
