#!/usr/bin/env python3
"""Summarise a .tcraft project or a mesh file from `texturecraft-cli info`.

Project: the project's normal format (from project.json), texture sets (index, name,
resolution, baked maps), each set's layer tree with masks and fill channels, high-poly and
cage meshes, and the mesh. `info` has no UV report for a project; inspect the mesh file.
Mesh (.glb .fbx .obj …): texture sets, materials, triangles and the UV report, plus the
embedded images and texture links of a .glb.

  tc_inspect.py crate.tcraft
  tc_inspect.py model.glb --json-out model-info.json
  tc_inspect.py crate.tcraft --full        # include each layer's fill sources and mask effects
"""
import argparse
import json
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tclib  # noqa: E402


def project_json(path):
    """The project.json inside a .tcraft zip (holds settings `info` does not report)."""
    try:
        with zipfile.ZipFile(path) as z:
            return json.loads(z.read("project.json"))
    except (zipfile.BadZipFile, KeyError, ValueError):
        return {}


def layer_tree(layers, full):
    out = []
    for l in layers or []:
        n = {"id": l["id"], "name": l["name"], "kind": l["kind"], "visible": l.get("visible", True)}
        if l.get("fill"):
            srcs = l["fill"].get("sources", {})
            n["fill"] = srcs if full else sorted(srcs)
        if l.get("mask"):
            m = l["mask"]
            n["mask"] = {"background": m.get("background"), "enabled": m.get("enabled"),
                         "effects": m.get("effects") if full else [
                             (e.get("generator") or {}).get("type") or e.get("name") or e.get("kind") for e in m.get("effects", [])]}
        if l.get("children"):
            n["children"] = layer_tree(l["children"], full)
        out.append(n)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", help=".tcraft project or mesh file")
    ap.add_argument("--full", action="store_true", help="include fill sources and mask effect settings")
    ap.add_argument("--json-out", help="also write the raw `info` JSON here")
    a = ap.parse_args()

    if not os.path.exists(a.file):
        raise tclib.TcError("not found: %s" % a.file)
    d = tclib.info(a.file)
    if a.json_out:
        with open(a.json_out, "w") as f:
            json.dump(d, f, indent=2)

    if d.get("kind") != "project":
        out = {"file": a.file, "kind": d.get("kind"), "textureSets": d.get("textureSets"),
               "materials": d.get("materials"), "triangles": d.get("triangles"),
               "vertices": d.get("vertices"), "uv": d.get("uv")}
        if a.file.lower().endswith(".glb"):
            out["glb"] = tclib.glb_summary(a.file)
        tclib.emit(out)

    sets = []
    for t in d["textureSets"]:
        ts = t["index"]
        sets.append({
            "index": ts, "name": t["name"], "resolution": t["resolution"], "size": t.get("size"),
            "uvTiles": t.get("uvTiles"), "channels": [c["channel"] for c in t.get("channels", [])],
            "baked": t.get("baked"),
            "parts": t.get("parts"),
            "layers": layer_tree(tclib.command(a.file, "layer.list", {"ts": ts}), a.full),
        })
    tclib.emit({"file": a.file, "kind": "project", "version": tclib.version(), "mesh": d.get("mesh"),
                "uv": d.get("uv"), "bakeMeshes": d.get("bakeMeshes"),
                "activeTextureSet": d.get("activeTextureSet"),
                "normalFormat": project_json(a.file).get("normal_format"), "textureSets": sets})


if __name__ == "__main__":
    tclib.main_guard(main)
