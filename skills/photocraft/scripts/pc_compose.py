#!/usr/bin/env python3
"""Build a layered PhotoCraft composition from a JSON spec, headless.

Usage:
  pc_compose.py SPEC.json [--overwrite] [--dry-run]

Spec (paths relative to the spec file; see references/recipes.md for a full example):
  {
    "canvas": {"width": 1080, "height": 1080, "background": "white"},  # or "open": "template.psd"
    "layers": [                       # bottom to top
      {"image": "bg.jpg", "fit": "cover", "name": "Photo"},
      {"image": "logo.png", "width": 180, "anchor": "top-right", "margin": 40, "name": "Logo"},
      {"fill": "#000000", "rect": [0, 700, 1080, 380], "opacity": 0.4, "name": "Shade"},
      {"gradient": {"from": "#000000", "to": "#ffffff", "angle": 90}, "name": "Ramp"},
      {"adjustment": "curves", "params": {"points": [[0, 0], [128, 150], [255, 255]]}},
      {"text": "Summer Sale", "size": 96, "color": "#ffffff", "anchor": "bottom-left",
       "margin": 80, "name": "Headline", "style": {"dropShadow": {"distance": 6, "size": 12}}},
      {"cmd": "filter.blur.gaussianBlur", "params": {"radius": 2}}       # raw step, active layer
    ],
    "save": ["post.psd", {"path": "post.jpg", "quality": 90}],
    "preview": "preview.png"
  }

Image sizing: "scale" (%), "width"/"height" (px, aspect kept) or "fit": "cover"|"contain".
Placement: "anchor" (top-left, top, top-right, left, center, right, bottom-left, bottom,
bottom-right) with "margin" (px or [x, y]), or "at": [x, y] for the top-left corner.
Images default to the canvas centre. Text without anchor/at uses "x"/"y" (baseline).
Every layer may set name, opacity (0..1), blend, visible and style
({"dropShadow"|"stroke"|"outerGlow"|...: params} -> layer.layerStyle.<kind>).

Prints a JSON summary (layers with ids and bounds [x, y, w, h], saved files, preview).
Refuses to overwrite existing outputs or the opened template unless --overwrite.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pclib import PcError, Session, die, info, to_step, walk  # noqa: E402

ANCHORS = {
    "top-left": (0, 0), "top": (1, 0), "top-right": (2, 0),
    "left": (0, 1), "center": (1, 1), "right": (2, 1),
    "bottom-left": (0, 2), "bottom": (1, 2), "bottom-right": (2, 2),
}


def anchored_origin(anchor, margin, size, canvas):
    """Top-left corner of a box of `size` anchored on `canvas` with `margin`."""
    if anchor not in ANCHORS:
        raise PcError("unknown anchor %r (use %s)" % (anchor, ", ".join(ANCHORS)))
    col, row = ANCHORS[anchor]
    mx, my = (margin, margin) if not isinstance(margin, list) else margin
    w, h = size
    cw, ch = canvas
    x = [mx, (cw - w) / 2.0, cw - w - mx][col]
    y = [my, (ch - h) / 2.0, ch - h - my][row]
    return x, y


def box(bounds):
    """[x0, y0, x1, y1] (command replies) -> (x, y, w, h)."""
    x0, y0, x1, y1 = bounds
    return x0, y0, x1 - x0, y1 - y0


class Composer(object):
    def __init__(self, spec, base, session):
        self.spec = spec
        self.base = base
        self.s = session
        self.canvas = None

    def path(self, rel):
        return os.path.abspath(os.path.join(self.base, os.path.expanduser(rel)))

    def target_origin(self, item, size):
        if "at" in item:
            return tuple(item["at"])
        if "anchor" in item:
            return anchored_origin(item["anchor"], item.get("margin", 0), size, self.canvas)
        return None

    def image(self, item):
        src = self.path(item["image"])
        native = info(src)
        nw, nh = float(native["width"]), float(native["height"])
        cw, ch = self.canvas
        if "scale" in item:
            scale = float(item["scale"])
        elif item.get("fit") == "cover":
            scale = max(cw / nw, ch / nh) * 100
        elif item.get("fit") == "contain":
            scale = min(cw / nw, ch / nh) * 100
        elif "width" in item:
            scale = item["width"] / nw * 100
        elif "height" in item:
            scale = item["height"] / nh * 100
        else:
            scale = 100.0
        size = (nw * scale / 100, nh * scale / 100)
        params = {"path": src, "scale": scale, "fit": False}
        origin = self.target_origin(item, size)
        if origin:
            params["center"] = [origin[0] + size[0] / 2.0, origin[1] + size[1] / 2.0]
        result = self.s.call("doc.place", params)
        return result["layer"]

    def text(self, item):
        params = {"x": item.get("x", 0), "y": item.get("y", item.get("size", 12))}
        for key in ("text", "box", "align", "orientation", "font", "size", "color", "tracking", "leading"):
            if key in item:
                params[key] = item[key]
        if "name" in item:
            params["name"] = item["name"]
        result = self.s.execute("type.create", params)
        layer = result["layer"]
        x, y, w, h = box(result["bounds"])
        origin = self.target_origin(item, (w, h))
        if origin:
            dx, dy = int(round(origin[0] - x)), int(round(origin[1] - y))
            if dx or dy:
                self.s.execute("layer.translate", {"layer": layer, "dx": dx, "dy": dy})
        return layer

    def fill(self, item, gradient=False):
        rect = item.get("rect")
        if rect is None and "size" in item:
            ox, oy = self.target_origin(item, tuple(item["size"])) or (0, 0)
            rect = [ox, oy, item["size"][0], item["size"][1]]
        if rect:
            self.s.execute("select.rect", {
                "x": int(round(rect[0])), "y": int(round(rect[1])),
                "width": int(round(rect[2])), "height": int(round(rect[3])),
                "ellipse": bool(item.get("ellipse"))})
        if gradient:
            result = self.s.execute("layer.newFillLayer.gradient", item["gradient"])
        else:
            result = self.s.execute("layer.newFillLayer.solidColor", {"color": item["fill"]})
        if rect:
            self.s.execute("select.deselect", {})
        return result["layer"]

    def adjustment(self, item):
        result = self.s.execute("layer.newAdjustmentLayer." + item["adjustment"], item.get("params") or {})
        return result["layer"]

    def finish_layer(self, layer, item):
        props = {}
        if "name" in item and "text" not in item:
            props["name"] = item["name"]
        if "opacity" in item:
            value = float(item["opacity"])
            props["opacity"] = value / 100.0 if value > 1 else value
        for key in ("blend", "visible"):
            if key in item:
                props[key] = item[key]
        if props:
            props["layer"] = layer
            self.s.execute("layer.setProps", props)
        for kind, params in (item.get("style") or {}).items():
            params = dict(params or {})
            params.setdefault("layer", layer)
            self.s.execute("layer.layerStyle." + kind, params)

    def run(self, outputs, preview):
        spec = self.spec
        if "open" in spec:
            opened = self.s.call("doc.open", {"path": self.path(spec["open"])})
            self.canvas = (opened["width"], opened["height"])
        else:
            canvas = dict(spec.get("canvas") or {})
            self.s.call("doc.new", canvas)
            self.canvas = (canvas.get("width", 1920), canvas.get("height", 1080))
        for item in spec.get("layers") or []:
            if "cmd" in item or "method" in item:
                method, params = to_step(item)
                self.s.call(method, params)
                continue
            if "image" in item:
                layer = self.image(item)
            elif "text" in item:
                layer = self.text(item)
            elif "fill" in item:
                layer = self.fill(item)
            elif "gradient" in item:
                layer = self.fill(item, gradient=True)
            elif "adjustment" in item:
                layer = self.adjustment(item)
            else:
                raise PcError("layer needs image, text, fill, gradient, adjustment or cmd: %s" % json.dumps(item))
            self.finish_layer(layer, item)
        saved = []
        for out in outputs:
            params = dict(out)
            saved.append(self.s.call("doc.save", params))
        rendered = None
        if preview:
            rendered = self.s.call("doc.render", {"path": preview, "maxSide": 1024})
        doc = self.s.call("doc.inspect", {})
        layers = [{"id": l["id"], "name": l["name"], "kind": l["kind"], "visible": l["visible"],
                   "bounds": l.get("bounds"), "depth": d} for d, l in walk(doc.get("layers") or [])]
        names = [l["name"] for l in layers]
        dupes = sorted(set(n for n in names if names.count(n) > 1))
        warnings = ["duplicate layer names %s: rename them so later edits can address them" % dupes] if dupes else []
        return {"size": [doc["width"], doc["height"]], "layers": layers,
                "saved": saved, "preview": rendered, "warnings": warnings}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("spec")
    parser.add_argument("--overwrite", action="store_true", help="allow replacing existing outputs")
    parser.add_argument("--dry-run", action="store_true", help="build and report, save nothing")
    parser.add_argument("--read-root", help="default: common folder of the spec and its inputs")
    parser.add_argument("--write-root", help="default: common folder of the outputs")
    args = parser.parse_args()

    try:
        with open(args.spec) as handle:
            spec = json.load(handle)
    except (OSError, ValueError) as exc:
        die("cannot read spec: %s" % exc)
    base = os.path.dirname(os.path.abspath(args.spec))

    def resolve(rel):
        return os.path.abspath(os.path.join(base, os.path.expanduser(rel)))

    outputs = []
    if not args.dry_run:
        for out in spec.get("save") or []:
            out = {"path": out} if isinstance(out, str) else dict(out)
            out["path"] = resolve(out["path"])
            outputs.append(out)
    preview = resolve(spec["preview"]) if spec.get("preview") and not args.dry_run else None
    inputs = [resolve(spec["open"])] if "open" in spec else []
    inputs += [resolve(i["image"]) for i in spec.get("layers") or [] if "image" in i]
    targets = [o["path"] for o in outputs] + ([preview] if preview else [])

    for target in targets:
        if target in inputs:
            die("output %s is also an input; write to a new file" % target)
        if os.path.exists(target) and not args.overwrite:
            die("%s exists; pass --overwrite to replace it" % target)
        os.makedirs(os.path.dirname(target), exist_ok=True)

    read_root = args.read_root or os.path.commonpath(inputs + [base])
    write_root = args.write_root or (os.path.commonpath([os.path.dirname(t) for t in targets]) if targets else base)
    try:
        with Session(read_root, write_root) as session:
            summary = Composer(spec, base, session).run(outputs, preview)
    except PcError as exc:
        die(str(exc))
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
