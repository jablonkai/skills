#!/usr/bin/env python3
"""Export a MaterialCraft graph's outputs (and optionally a portable .mcmat) and prove the result.

  mc_export.py IN.sbs DIR [--graph N] [--set ID=VALUE]... [--format png] [--depth 16]
               [--pattern '$(graph)_$(identifier)'] [--mcmat OUT.mcmat [--mcmat-size N]]
               [--texturecraft-check] [--overwrite]

Checks before exporting: every --set names an exposed input, the pattern uses only the tokens the
engine knows ($(graph), $(identifier), $(usage); others turn into `_name_` silently), and the
format can hold the requested depth. After: one file per output node, each decodes at the graph
size with the requested bit depth (PNG, TIFF header, EXR pixel type). With --mcmat it writes the
material through file.exportMaterial and checks the zip's material.json, maps and parameter
values; --texturecraft-check loads that .mcmat into a fresh TextureCraft project headless.
Prints JSON; exits 1 on any failed check. The input package is never written.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mclib as m  # noqa: E402

TOKENS = {"graph", "identifier", "usage"}
# What each format really writes in 0.4.1 (a --depth outside the set is ignored silently).
DEPTHS = {"png": {8, 16}, "tif": {8, 16}, "exr": {32}, "hdr": {32},
          "jpg": {8}, "bmp": {8}, "tga": {8}, "webp": {8}}


def parse_sets(sets):
    out = {}
    for s in sets or []:
        k, eq, v = s.partition("=")
        if not eq:
            raise m.McError("--set %s: write ID=VALUE" % s)
        try:
            out[k] = json.loads(v)
        except ValueError:
            out[k] = v  # bare words and "#rrggbb" are strings
    return out


def texturecraft_check(mcmat):
    tc = shutil.which("texturecraft-cli") or os.path.expanduser("~/.local/bin/texturecraft-cli")
    if not os.access(tc, os.X_OK):
        return {"ok": False, "error": "texturecraft-cli not found"}
    tmp = tempfile.mkdtemp(prefix="mc-tc-")
    proj, out = os.path.join(tmp, "check.tcraft"), os.path.join(tmp, "loaded.tcraft")

    def tcrun(args):
        p = subprocess.run([tc] + args, capture_output=True, text=True, timeout=600)
        if p.returncode != 0:
            raise m.McError("texturecraft-cli %s: %s" % (args[0], (p.stderr or p.stdout).strip()[:300]))
        return p.stdout

    tcrun(["new", "builtin:sphere", proj])
    res = tcrun(["run", proj, "material.load", json.dumps({"path": os.path.abspath(mcmat)}), "-o", out])
    layer = json.loads("\n".join(l for l in res.splitlines() if not l.startswith("saved "))).get("layer")
    layers = json.loads(tcrun(["run", out, "layer.list", "{}"]))
    linked = [{"id": l.get("id"), "name": l.get("name"), "graph": l["fill"]["link"].get("graph")}
              for l in layers if isinstance(l.get("fill"), dict) and l["fill"].get("link")]
    return {"ok": layer is not None and bool(linked), "layer": layer, "linked_layers": linked,
            "version": tcrun(["--version"]).strip()}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inp", help=".sbs package (or `sample`)")
    ap.add_argument("dir", help="output folder (must be new or empty unless --overwrite)")
    ap.add_argument("--graph", type=int, help="graph index (default: the open graph)")
    ap.add_argument("--set", action="append", metavar="ID=VALUE", help="exposed input value (JSON or #rrggbb)")
    ap.add_argument("--format", default="png", choices=sorted(DEPTHS))
    ap.add_argument("--depth", type=int, choices=[8, 16, 32])
    ap.add_argument("--pattern", help="file-name pattern, e.g. '$(graph)_$(identifier)'")
    ap.add_argument("--mcmat", help="also write a portable .mcmat material here")
    ap.add_argument("--mcmat-size", type=int, help=".mcmat map size in px (power of two)")
    ap.add_argument("--texturecraft-check", action="store_true", help="load the .mcmat into TextureCraft headless")
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args()

    g = m.graph_of(a.inp, a.graph)
    outs = m.outputs(g)
    values = parse_sets(a.set)
    exposed = {e["id"] for e in g.get("exposed", [])}
    problems = ["--set %s: no exposed input (has %s)" % (k, sorted(exposed)) for k in values if k not in exposed]
    if a.pattern:
        bad = [t for t in re.findall(r"\$\((\w+)\)", a.pattern) if t not in TOKENS]
        if bad:
            problems.append("pattern tokens %s are not known; use $(graph), $(identifier), $(usage)" % bad)
    if a.depth and a.depth not in DEPTHS[a.format]:
        problems.append("%s is written at %s-bit only, not %d; the CLI would ignore --depth silently"
                        % (a.format, "/".join(map(str, sorted(DEPTHS[a.format]))), a.depth))
    if not outs:
        problems.append("graph `%s` has no output nodes; nothing would be exported" % g["name"])
    if a.mcmat:
        m.refuse_overwrite(a.mcmat, a.overwrite, ".mcmat")
    if problems:
        m.emit({"ok": False, "problems": problems}, ok=False)
    m.refuse_overwrite(a.dir, a.overwrite, "folder")

    args = ["export", a.inp, a.dir, "--format", a.format]
    if a.graph is not None:
        args += ["--graph", str(a.graph)]
    if a.depth:
        args += ["--depth", str(a.depth)]
    if a.pattern:
        args += ["--pattern", a.pattern]
    for k, v in values.items():
        args += ["--set", "%s=%s" % (k, json.dumps(v))]  # --set takes JSON: "#rrggbb" needs its quotes
    files = m.run_json(args)["files"]

    fails, report = [], []
    n_img = len([o for o in outs if not o["value"]])  # value outputs write no file
    if len(files) != n_img:
        fails.append("%d files for %d image outputs" % (len(files), n_img))
    if len(set(files)) != len(files):
        fails.append("file names collide (the pattern needs $(identifier) or $(usage))")
    want = tuple(g["size"])
    for f in files:
        try:
            h = m.image_header(f)
        except (m.McError, OSError) as e:
            fails.append("%s: %s" % (f, e))
            continue
        row = {"file": f, "size": [h["width"], h["height"]], "channels": h["channels"], "bit_depth": h["bit_depth"]}
        if h["width"] is not None and (h["width"], h["height"]) != want:
            fails.append("%s is %sx%s, graph is %sx%s" % (f, h["width"], h["height"], want[0], want[1]))
        if a.depth and h["bit_depth"] is not None and h["bit_depth"] != a.depth:
            fails.append("%s is %s-bit, asked for %d" % (f, h["bit_depth"], a.depth))
        report.append(row)
    for o in outs:
        if o["value"]:
            continue
        hit = [f for f in files if o["identifier"] in os.path.basename(f)
               or o["usage"].replace(" ", "").lower() in os.path.basename(f).lower()]
        if a.pattern and "$(identifier)" in a.pattern and not hit:
            fails.append("no file for output `%s`" % o["identifier"])

    result = {"ok": not fails, "graph": g["name"], "size": list(want), "format": a.format, "depth": a.depth,
              "values": values, "outputs": [o["identifier"] for o in outs], "files": report}

    if a.mcmat:
        p = {"path": os.path.abspath(a.mcmat)}
        if a.graph is not None:
            p["graph"] = a.graph
        if a.mcmat_size:
            p["size"] = a.mcmat_size
        if values:
            p["values"] = values
        m.command(a.inp, "file.exportMaterial", p)
        with zipfile.ZipFile(a.mcmat) as z:
            names = z.namelist()
            meta = json.loads(z.read("material.json"))
        maps = [mp["usage"] for mp in meta.get("maps", [])]
        missing = [mp["file"] for mp in meta.get("maps", []) if mp["file"] not in names]
        if missing:
            fails.append(".mcmat lacks %s" % missing)
        if not maps:
            fails.append(".mcmat has no maps")
        params = {pr["id"]: pr.get("value") for pr in meta.get("parameters", [])}
        for k in values:
            if k not in params:
                fails.append(".mcmat has no parameter `%s`" % k)
        result["mcmat"] = {"path": a.mcmat, "maps": maps, "size": meta.get("size"),
                           "parameters": params, "presets": [pr["name"] for pr in meta.get("presets", [])],
                           "source": ("source.sbs" in names) or ("source.mcraft" in names)}
        if a.texturecraft_check:
            tc = texturecraft_check(a.mcmat)
            result["texturecraft"] = tc
            if not tc.get("ok"):
                fails.append("TextureCraft did not load the .mcmat: %s" % tc.get("error"))
    elif a.texturecraft_check:
        fails.append("--texturecraft-check needs --mcmat")
    result["ok"] = not fails
    result["failed"] = fails
    m.emit(result, ok=not fails)


if __name__ == "__main__":
    m.main_guard(main)
