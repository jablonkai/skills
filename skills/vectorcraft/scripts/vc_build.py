#!/usr/bin/env python3
"""Build a VectorCraft document from a JSON spec, save it and export it.

    vc_build.py SPEC.json [--overwrite] [--dry-run]

Spec (all lengths in document units; object x/y are relative to their artboard's top-left):
{
  "units": "Pixels",                       # Pixels (default) | Points | Millimeters | …
  "colorMode": "rgb",                      # rgb (default) | cmyk
  "spacing": 40,                           # gap between artboards laid out in a row
  "artboards": [{"name": "Icon 1024", "width": 1024, "height": 1024}, …],
  "swatches": [{"name": "Brand", "color": "#e4572e", "global": true}],
  "layers": ["Mark", "Wordmark"],          # bottom to top; first one renames Layer 1
  "objects": [                             # back to front
    {"artboard": 0, "layer": "Mark", "name": "Disc", "shape": "ellipse",
     "x": 112, "y": 112, "width": 800, "height": 800, "fill": {"swatch": "Brand"}},
    {"shape": "rectangle"|"polygon"|"star"|"line", …draw_shape params},
    {"path": "M0 0 L10 0 Z", …},           # SVG path data (draw_path d)
    {"text": "ACME", "x": 512, "y": 900, "size": 120, "font": "Helvetica",
     "style": "Bold", "color": "#222222", "justify": "center"},
    {"symbol": "Logo", "x": …, "y": …},    # place an instance of a symbol made by "makeSymbol"
    {"cmd": "object.align", "params": {…}} # raw engine command
  ],
  "save": "out/logo.vectorcraft",
  "exports": [
    {"path": "out/icon-{index}.png", "artboards": "each", "scale": 1},   # {index} {name}
    {"path": "out/sheet.pdf"},                                           # every artboard
    {"path": "out/mark.svg", "artboard": 0, "outlineText": true}
  ],
  "preview": "out/preview"                 # a PNG per artboard: <prefix>-<index>.png
}

Shapes get stroke "none" unless the spec gives one (VectorCraft's default new-art
appearance is a white fill with a 1 pt black stroke). Objects can carry "name",
"opacity", "strokeWidth", "dash", "effects". A shape or text object may set
"makeSymbol": "Name" to turn itself into a symbol. Refuses to overwrite outputs unless
--overwrite. Prints a JSON report with the created ids and the info read-back.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vclib import Session, ToolError, info, refuse_existing  # noqa: E402

SHAPE_KEYS = {"x", "y", "width", "height", "radius", "rotation", "cx", "cy", "sides",
              "radius1", "radius2", "points", "x1", "y1", "x2", "y2"}
PAINT_KEYS = {"fill", "stroke", "strokeWidth", "dash", "cap", "join", "opacity", "name", "effects"}
TEXT_KEYS = {"size", "font", "style", "color", "justify", "area", "vertical"}


def expand_exports(spec, artboards):
    out = []
    for e in spec.get("exports", []):
        e = dict(e)
        e["path"] = os.path.abspath(os.path.expanduser(e["path"]))
        if e.pop("artboards", None) == "each":
            for i, ab in enumerate(artboards):
                one = dict(e, artboard=i)
                one["path"] = e["path"].replace("{index}", str(i + 1)).replace(
                    "{name}", ab.get("name", "Artboard %d" % (i + 1)).replace("/", "-"))
                out.append(one)
        else:
            out.append(e)
    return out


def offset(obj, ab):
    """Artboard-relative x/y/cx/cy/x1… to document coordinates."""
    o = dict(obj)
    for k in ("x", "cx", "x1", "x2"):
        if k in o:
            o[k] = o[k] + ab["x"]
    for k in ("y", "cy", "y1", "y2"):
        if k in o:
            o[k] = o[k] + ab["y"]
    return o


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="print the plan, write nothing")
    a = ap.parse_args()
    spec = json.load(open(a.spec))
    base = os.path.dirname(os.path.abspath(a.spec))
    os.chdir(base)  # relative paths in the spec are relative to the spec file

    spacing = spec.get("spacing", 40)
    artboards, x = [], 0.0
    for ab in spec.get("artboards") or [{"width": 1024, "height": 1024}]:
        artboards.append(dict(ab, x=x, y=0.0))
        x += ab["width"] + spacing
    exports = expand_exports(spec, artboards)
    save = os.path.abspath(spec["save"]) if spec.get("save") else None
    previews = []
    if spec.get("preview"):
        prefix = os.path.abspath(spec["preview"])
        previews = ["%s-%d.png" % (prefix, i + 1) for i in range(len(artboards))]
    outputs = [p for p in [save] + [e["path"] for e in exports] + previews if p]
    if a.dry_run:
        print(json.dumps({"artboards": artboards, "outputs": outputs}, indent=1))
        return 0
    refuse_existing(outputs, a.overwrite)
    for p in outputs:
        os.makedirs(os.path.dirname(p), exist_ok=True)
    root = os.path.commonpath([os.path.dirname(p) for p in outputs] + [base])

    s = Session(root, root)
    report = {"ids": {}, "outputs": []}
    try:
        first = artboards[0]
        s.cmd("file.new", {"width": first["width"], "height": first["height"],
                           "units": spec.get("units", "Pixels"), "artboards": 1,
                           "name": os.path.splitext(os.path.basename(save or "Untitled"))[0]})
        if spec.get("colorMode", "rgb").lower() == "cmyk":
            s.cmd("file.documentColorMode", {"mode": "cmyk"})
        s.cmd("artboard.setProps", {"index": 0, "name": first.get("name", "Artboard 1")})
        for i, ab in enumerate(artboards[1:], start=1):
            s.cmd("artboard.new", {"x": ab["x"], "y": ab["y"], "width": ab["width"],
                                   "height": ab["height"], "name": ab.get("name", "Artboard %d" % (i + 1))})
        for sw in spec.get("swatches", []):
            s.cmd("swatch.new", sw)

        layers = {}
        current = s.tool("doc_inspect", {"depth": 1})["currentLayer"]
        for i, name in enumerate(spec.get("layers", [])):
            if i == 0:
                s.cmd("layer.setProps", {"id": current, "name": name})
                layers[name] = current
            else:
                layers[name] = s.cmd("layer.new", {"name": name, "top": True})["id"]

        for n, obj in enumerate(spec.get("objects", [])):
            if "cmd" in obj:
                s.cmd(obj["cmd"], obj.get("params", {}))
                continue
            ab = artboards[obj.get("artboard", 0)]
            if obj.get("layer"):
                s.cmd("layer.setCurrent", {"id": layers[obj["layer"]]})
            o = offset(obj, ab)
            if "shape" in o:
                args = {k: v for k, v in o.items() if k in SHAPE_KEYS | PAINT_KEYS}
                args["shape"] = o["shape"]
                args.setdefault("stroke", "none")
                oid = s.tool("draw_shape", args)
            elif "path" in o:
                # Path data can't be offset key by key: draw it in artboard space, then
                # move it by the artboard's position.
                args = {k: v for k, v in obj.items() if k in PAINT_KEYS | {"closed", "points"}}
                args["d"] = obj["path"]
                args.setdefault("stroke", "none")
                oid = s.tool("draw_path", args)
                pid = oid["id"] if isinstance(oid, dict) else oid
                if ab["x"] or ab["y"]:
                    s.tool("transform", {"ids": [pid], "dx": ab["x"], "dy": ab["y"]})
            elif "text" in o:
                params = {k: v for k, v in o.items() if k in TEXT_KEYS | {"x", "y", "text"}}
                oid = s.cmd("text.create", params)
                if obj.get("name"):
                    s.cmd("object.setProps", {"id": oid["id"], "name": obj["name"]})
                if "opacity" in obj:
                    s.cmd("object.setProps", {"id": oid["id"], "opacity": obj["opacity"]})
            elif "symbol" in o:
                oid = s.cmd("symbol.place", {"name": o["symbol"], "x": o["x"], "y": o["y"]})
            else:
                raise ToolError("object %d: needs shape, path, text, symbol or cmd" % n)
            oid = oid["id"] if isinstance(oid, dict) else oid
            report["ids"][obj.get("name") or "#%d" % n] = oid
            if obj.get("makeSymbol"):
                s.cmd("symbol.new", {"name": obj["makeSymbol"], "ids": [oid]})

        if save:
            report["outputs"].append(s.tool("save_file", {"path": save}))
        for e in exports:
            report["outputs"].append(s.tool("export", e))
        for i, p in enumerate(previews):
            report["outputs"].append(s.cmd("document.export", {"path": p, "format": "png", "artboard": i}))
    except ToolError as e:
        print(json.dumps({"error": str(e), "partial": report}, indent=1))
        return 1
    finally:
        s.close()

    if save:
        d = info(save)
        report["info"] = {"artboards": [[ab["name"]] + ab["rect"][2:] for ab in d["artboards"]],
                          "kinds": d["kinds"], "warnings": d["warnings"],
                          "fonts": ["%s %s: %s" % (f["family"], f["style"], f["status"]) for f in d["fonts"]]}
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
