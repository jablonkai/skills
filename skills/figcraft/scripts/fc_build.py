#!/usr/bin/env python3
"""Build a FigCraft design from a JSON spec in one headless session, then save and export.

    fc_build.py SPEC.json [--root DIR] [--overwrite]

Spec (paths relative to the spec file; see references/recipes.md for a full example):
    {
      "styles": {"paint": {"Brand/Primary": "#2563EB"},
                 "text":  {"H1": {"fontFamily": "Inter", "fontStyle": "Bold", "fontSize": 28}}},
      "components": [ NODE, … ],          top-level main components (type defaults to component)
      "frames":     [ NODE, … ],          top-level frames (type defaults to frame)
      "save": "login.figcraft",
      "exports": [{"node": "Login", "path": "login@2x.png", "scale": 2},
                  {"node": "Login", "path": "login.svg"},
                  {"frames": "each", "dir": "png", "format": "png", "scale": 1},
                  {"node": "Card", "path": "card.pdf", "bleed": "3mm", "cropMarks": true}],
      "preview": "preview.png"
    }
NODE: {"type": frame|text|rectangle|ellipse|component|…, "name", "x", "y", "width",
       "height", "text" (text layers), "props" {node.set keys: fill, layout, gap, padding,
       cornerRadius, fontSize, sizingH, …}, "style" (text style name), "fillStyle" (paint
       style name), "children": [NODE, …]}
     or {"instance": "Button", "name", "x", "y", "props", "text": {"Label": "Sign in"},
         "variant": {"Style": "Secondary"}}
       — an instance of a component from "components"; "text" overrides the instance's
       text layers by name, "variant" picks a variant of a component set.
A component set: {"name": "Button", "width", "height", "variants": [NODE named
"Style=Primary", NODE named "Style=Secondary", …]} — the variants are laid out in a row
and combined; instances start on the first variant.
Top-level layers without x/y are placed in a row, 100 apart. Inside an auto-layout parent
the layout positions children; in a vertical one, a child without "width" or a sizingH
prop gets sizingH "fill", so it stretches with the screen (text then wraps). Prints the created ids by name and an info read-back.
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fclib import Session, ToolError, cli, flatten, info, refuse_existing  # noqa: E402

NODE_KEYS = ("name", "x", "y", "width", "height", "text", "path", "props")


class Builder:
    def __init__(self):
        self.commands = []   # batch steps
        self.names = []      # (step index, display name)
        self.components = {}  # name -> step index
        self.styled = []     # (step, style name, target)
        self.overrides = []  # (instance step, {child name: text})

    def add(self, command, params, label):
        self.commands.append({"command": command, "params": params})
        self.names.append(label)
        return len(self.commands) - 1

    def node(self, spec, parent=None, default_type="frame", path="", stack=False):
        """stack: the parent is a vertical auto layout, so a child without a width or
        sizingH stretches to the parent's width (sizingH fill), as UI layouts expect."""
        label = (path + "/" if path else "") + spec.get("name", spec.get("instance", "?"))
        if stack and "width" not in spec and "sizingH" not in spec.get("props", {}):
            spec = dict(spec, props=dict(spec.get("props", {}), sizingH="fill"))
        if "instance" in spec:
            comp = spec["instance"]
            if comp not in self.components:
                raise SystemExit("instance of unknown component %r (define it under components)" % comp)
            params = {"component": {"$step": self.components[comp]}}
            for k in ("x", "y"):
                if k in spec:
                    params[k] = spec[k]
            if parent is not None:
                params["parent"] = {"$step": parent}
            step = self.add("instance.create", params, label)
            if spec.get("variant"):
                self.add("instance.setProperties", {"ids": [{"$step": step}], "properties": spec["variant"]},
                         label + " (props)")
            props = dict(spec.get("props", {}))
            if "name" in spec:
                props["name"] = spec["name"]
            if props:
                self.add("node.set", dict(props, ids=[{"$step": step}]), label + " (props)")
            if spec.get("text"):
                self.overrides.append((step, spec["text"]))
            return step
        params = {"type": spec.get("type", default_type)}
        params.update({k: spec[k] for k in NODE_KEYS if k in spec})
        if parent is not None:
            params["parent"] = {"$step": parent}
        step = self.add("node.create", params, label)
        if spec.get("style"):
            self.styled.append((step, spec["style"], None))
        if spec.get("fillStyle"):
            self.styled.append((step, spec["fillStyle"], "fill"))
        vertical = spec.get("props", {}).get("layout") == "vertical"
        for child in spec.get("children", []):
            self.node(child, step, "frame", label, stack=vertical)
        return step


def place_row(specs, start_x=0, gap=100):
    """Give top-level specs without x/y a position in a row; return the next free x."""
    x = start_x
    for spec in specs:
        if "x" not in spec and "y" not in spec:
            spec["x"], spec["y"] = x, 0
        x = max(x, spec.get("x", 0) + spec.get("width", 100) + gap)
    return x


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--root", help="file-access root (default: the spec's folder)")
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args()
    base = os.path.dirname(os.path.abspath(a.spec))
    spec = json.load(open(a.spec))

    def out(p):
        return p if os.path.isabs(p) else os.path.join(base, p)

    targets = [out(spec["save"])] if spec.get("save") else []
    targets += [out(e["path"]) for e in spec.get("exports", []) if "path" in e]
    if spec.get("preview"):
        targets.append(out(spec["preview"]))
    refuse_existing(targets, a.overwrite)

    b = Builder()
    frames = spec.get("frames", [])
    comps = spec.get("components", [])
    next_x = place_row(frames)
    place_row(comps, start_x=next_x + 100)
    for c in comps:
        if "variants" in c:
            # each variant is its own main component, then they are combined into a set
            variants = [dict(v, x=c.get("x", 0) + i * (c.get("width", 200) + 40), y=c.get("y", 0),
                             **{k: c[k] for k in ("width", "height") if k in c and k not in v})
                        for i, v in enumerate(c["variants"])]
            steps = [b.node(v, default_type="component", path=c["name"]) for v in variants]
            set_step = b.add("component.combineVariants", {"ids": [{"$step": s} for s in steps]}, c["name"])
            b.add("node.set", {"ids": [{"$step": set_step}], "name": c["name"]}, c["name"] + " (props)")
            b.components[c["name"]] = set_step
        else:
            b.components[c["name"]] = b.node(c, default_type="component")
    for f in frames:
        b.node(f, default_type="frame")

    s = Session(a.root or base)
    try:
        for name, value in spec.get("styles", {}).get("paint", {}).items():
            s.cmd("style.create", {"type": "paint", "name": name, "value": value})
        for name, value in spec.get("styles", {}).get("text", {}).items():
            s.cmd("style.create", {"type": "text", "name": name, "value": value})
        try:
            results = s.batch(b.commands, "fc_build")
        except ToolError as e:
            sys.exit("build failed (nothing was created): %s" % e)
        ids = [r.get("id") if isinstance(r, dict) else None for r in results]
        for step, style, target in b.styled:
            params = {"ids": [ids[step]], "style": style}
            if target:
                params["target"] = target
            s.cmd("style.apply", params)
        for step, texts in b.overrides:
            layers = flatten({"pages": [{"children": [s.tool("get_node", {"id": ids[step], "depth": 20})]}]})
            for child, chars in texts.items():
                hit = [n["id"] for n in layers if n["name"] == child and n["type"] == "TEXT"]
                if not hit:
                    sys.exit("instance %s has no text layer %r" % (b.names[step], child))
                s.cmd("node.set", {"ids": hit, "characters": chars})
        by_name = {}
        for step, label in enumerate(b.names):
            if ids[step] is not None and not label.endswith("(props)"):
                by_name[label] = ids[step]
        top = {n["name"]: n["id"] for n in s.tree(depth=1) if n["parent"] is None}

        if spec.get("save"):
            os.makedirs(os.path.dirname(out(spec["save"])), exist_ok=True)
            s.tool("save_file", {"path": out(spec["save"])})
        exported = []
        for e in spec.get("exports", []):
            opts = {k: v for k, v in e.items() if k not in ("node", "frames", "path", "dir")}
            if e.get("frames") == "each":
                d = out(e.get("dir", "."))
                os.makedirs(d, exist_ok=True)
                fmt = e.get("format", "png")
                for name, nid in top.items():
                    if name in b.components:
                        continue
                    p = os.path.join(d, "%s.%s" % (name.replace("/", "-"), fmt))
                    refuse_existing([p], a.overwrite)
                    exported.append(s.tool("export", dict(opts, ids=[nid], path=p, format=fmt)))
                continue
            node = e.get("node")
            nid = top.get(node) if node in top else by_name.get(node)
            if node and nid is None:
                sys.exit("export: no layer named %r (top-level: %s)" % (node, sorted(top)))
            p = out(e["path"])
            os.makedirs(os.path.dirname(p), exist_ok=True)
            exported.append(s.tool("export", dict(opts, path=p, **({"ids": [nid]} if nid else {}))))
    finally:
        s.close()

    report = {"ids": by_name, "exports": exported}
    if spec.get("save"):
        report["info"] = info(out(spec["save"]))
        if spec.get("preview"):
            subprocess.run([cli(), "render", out(spec["save"]), "-o", out(spec["preview"])],
                           capture_output=True, check=True)
            report["preview"] = out(spec["preview"])
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
