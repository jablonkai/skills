#!/usr/bin/env python3
"""Build an EffectCraft project from a JSON spec, headless, then save, preview and render.

Spec (paths are relative to the spec file):

  {
    "project": "out/lower-third.ecproj",
    "comp": {"name": "LT", "width": 1920, "height": 1080, "frameRate": 25, "duration": 5},
    "layers": [                                   # top of the stack first
      {"type": "text", "name": "Name", "text": "Jane Doe", "size": 64, "fill": "#ffffff",
       "justify": "left", "position": [160, 900],
       "keys": {"transform/position": [[0, [-700, 900]], [0.6, [160, 900]]]},
       "ease": "easyEase"},
      {"type": "shape", "name": "Bar", "kind": "rect", "size": [900, 120], "fill": "#00ADEF",
       "position": [610, 880], "props": {"transform/opacity": 90},
       "expressions": {"transform/rotation": "wiggle(1, 2)"},
       "effects": [{"effect": "Drop Shadow", "values": {"distance": 6}}]},
      {"type": "footage", "path": "clip.mp4", "name": "BG", "timing": {"start": 0}}
    ],
    "essential": [{"layer": "Name", "path": "text/sourceText", "name": "Name"}],
    "template": "out/lower-third.ectemplate",
    "preview": {"time": 2.0, "out": "out/preview.png", "transparent": true},
    "render": [{"out": "out/lt.mov", "format": "prores", "prores": "4444", "channels": "rgba"}]
  }

Layer types: text, shape, solid, null, adjustment, footage. Every other key of a layer is
passed to its create command (layer.newText / newShape / newSolid …; footage: layer.addItem).
`keys` times are comp seconds; `ease` is linear | easyEase | bezier | hold (default
easyEase). Nothing is saved when a step fails. Refuses to overwrite without --overwrite.
"""
import argparse
import json
import os
import sys

from eclib import Session, ToolError, refuse_existing, run_cli

CREATE = {"text": "layer.newText", "shape": "layer.newShape", "solid": "layer.newSolid",
          "null": "layer.newNull", "adjustment": "layer.newAdjustment"}
OWN_KEYS = {"type", "keys", "ease", "expressions", "props", "effects", "timing", "path"}
RENDER_FLAGS = {"format", "start", "end", "fps", "resolution", "quality", "channels",
                "prores", "bitrate", "audio", "jpeg-quality", "video-quality", "profile"}


def abspath(base, p):
    return os.path.abspath(os.path.join(base, os.path.expanduser(p)))


def build(spec, base, overwrite):
    project = abspath(base, spec["project"])
    template = abspath(base, spec["template"]) if spec.get("template") else None
    preview = spec.get("preview")
    renders = spec.get("render", [])
    outputs = [project] + ([template] if template else [])
    outputs += [abspath(base, preview["out"])] if preview else []
    outputs += [abspath(base, r["out"]) for r in renders]
    refuse_existing(outputs, overwrite)

    layers = spec.get("layers", [])
    footage = [abspath(base, l["path"]) for l in layers if l.get("type") == "footage"]
    write_roots = sorted({os.path.dirname(p) for p in outputs})
    for d in write_roots:
        os.makedirs(d, exist_ok=True)
    read_roots = sorted({base} | {os.path.dirname(p) for p in footage})

    s = Session(read_roots, write_roots)
    try:
        s.tool("open_project", {"new": True})
        comp = spec["comp"]
        s.cmd("comp.new", dict(comp, open=True))
        comp_name = comp.get("name")

        # Create bottom-first so the first spec entry ends on top of the stack.
        ids = {}
        steps, owners = [], []
        for i, layer in reversed(list(enumerate(layers))):
            kind = layer.get("type")
            params = {k: v for k, v in layer.items() if k not in OWN_KEYS}
            if kind == "footage":
                item = s.cmd("file.import", {"paths": [abspath(base, layer["path"])]})
                if not item.get("items"):
                    raise ToolError("import failed: %s %s" % (layer["path"], item.get("errors")))
                name = params.pop("name", None)
                steps.append({"command": "layer.addItem",
                              "params": dict(params, item=item["items"][0], index=1)})
                owners.append(i)
                if name:
                    steps.append({"command": "layer.rename",
                                  "params": {"layer": "$%d.layer" % len(steps), "name": name}})
                    owners.append(None)
            elif kind in CREATE:
                steps.append({"command": CREATE[kind], "params": params})
                owners.append(i)
            else:
                raise ToolError("layer %d: unknown type %r" % (i, kind))
        res = s.batch(steps, label="Build layers")["results"]
        for owner, r in zip(owners, res):
            if owner is not None:
                ids[owner] = r["layer"] if isinstance(r, dict) else r

        for i, layer in enumerate(layers):
            lid = ids[i]
            if layer.get("timing"):
                s.cmd("layer.timing", dict(layer["timing"], layers=[lid]))
            for path, value in (layer.get("props") or {}).items():
                s.tool("set_property", {"layer": lid, "path": path, "value": value})
            for path, keys in (layer.get("keys") or {}).items():
                s.tool("add_keyframe", {
                    "layer": lid, "path": path, "timeBase": "comp",
                    "keys": [{"time": t, "value": v} for t, v in keys],
                    "interpolation": layer.get("ease", "easyEase")})
            for path, expr in (layer.get("expressions") or {}).items():
                r = s.tool("set_property", {"layer": lid, "path": path, "expression": expr})
                if isinstance(r, dict) and r.get("expressionError"):
                    raise ToolError("expression on %s: %s" % (path, r["expressionError"]))
            for fx in layer.get("effects") or []:
                s.tool("add_effect", {"layer": lid, "effect": fx["effect"],
                                      "values": fx.get("values", {})})

        for ctl in spec.get("essential", []):
            s.cmd("essential.addProperty", dict(ctl, comp=comp_name))
        s.tool("save_project", {"path": project})
        if template:
            s.cmd("essential.exportTemplate", {"comp": comp_name, "path": template})
    finally:
        s.close()

    done = {"project": project, "comp": comp_name, "layers": len(layers)}
    if template:
        done["template"] = template
    if preview:
        out = abspath(base, preview["out"])
        args = ["render-frame", "--project", project, "--comp", comp_name,
                "--time", str(preview.get("time", 0)), "--out", out]
        if preview.get("transparent"):
            args.append("--transparent")
        run_cli(args)
        done["preview"] = out
    done["renders"] = []
    for r in renders:
        out = abspath(base, r["out"])
        args = ["render", "--project", project, "--comp", comp_name, "--out", out]
        for k, v in r.items():
            if k == "out":
                continue
            if k not in RENDER_FLAGS:
                raise ToolError("render: unknown option %r" % k)
            args += ["--" + k, str(v)]
        run_cli(args)
        done["renders"].append(out)
    return done


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", help="spec JSON file")
    ap.add_argument("--overwrite", action="store_true", help="replace existing outputs")
    a = ap.parse_args()
    with open(a.spec) as f:
        spec = json.load(f)
    try:
        print(json.dumps(build(spec, os.path.dirname(os.path.abspath(a.spec)), a.overwrite),
                         indent=2))
    except (ToolError, RuntimeError) as e:
        sys.exit("ec_build: %s" % e)


if __name__ == "__main__":
    main()
