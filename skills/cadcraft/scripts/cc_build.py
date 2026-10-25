#!/usr/bin/env python3
"""Build (or extend) a drawing from a JSON spec in one headless CADCraft session.

    cc_build.py SPEC.json [--overwrite]

Spec keys (all optional except "save"):
    "base":   "in.dxf"           open this drawing instead of starting a new one
    "metric": true               new drawing in mm (default true here; CADCraft's own
                                 default is imperial inches)
    "textHeight": 2.5            used for text/mtext/attdef without "height"
    "layers": [{"name": "GEOM", "color": "White", "linetype": "CENTER", "lineweight": 0.5}]
    "draw":   [{"layer": "GEOM", "cmd": "circle", "params": {...}, "as": "hole1"},
               {"layer": "DIM", "cmd": "dimdiameter", "params": {"handle": "@hole1", "at": [..]}},
               {"layer": "GEOM", "script": "LINE 0,0 10,0\\n\\n"}]
              "@name" in params is the handle of the item saved with "as": "name".
    "titleBlock": {"name": "TB", "at": [x, y], "size": [w, h], "layer": "TITLE",
                   "fields": [{"tag": "TITLE", "value": "Plate", "at": [5, 20], "height": 5}]}
    "save":   "out.dxf"          DXF or DWG
    "exports": [{"path": "out.pdf"}, {"path": "out.png", "window": [x0, y0, x1, y1]},
                {"path": "out.svg", "view": "extents"}]
               made with `cadcraft-cli convert` from the saved file, framing explicit.

Refuses to overwrite existing outputs (or the base) unless --overwrite. Prints the
handles created, the `info` read-back and the outputs as JSON; exits 1 on any error.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cclib import Session, ToolError, convert, info, same_file  # noqa: E402

TEXT_CMDS = ("text", "mtext", "attdef", "mleader", "leader")
REF = re.compile(r"^@([\w.-]+)$")


def resolve(value, named):
    if isinstance(value, str):
        m = REF.match(value)
        if m:
            if m.group(1) not in named:
                raise ToolError("unknown ref %s (no earlier item has \"as\": %r)" % (value, m.group(1)))
            return named[m.group(1)]
        return value
    if isinstance(value, list):
        return [resolve(v, named) for v in value]
    if isinstance(value, dict):
        return {k: resolve(v, named) for k, v in value.items()}
    return value


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args()
    spec_dir = os.path.dirname(os.path.abspath(a.spec))
    with open(a.spec) as f:
        spec = json.load(f)

    def p(path):
        return os.path.abspath(os.path.join(spec_dir, os.path.expanduser(path)))

    if "save" not in spec:
        sys.exit("spec needs \"save\": the exports are converted from the saved drawing")
    save = p(spec["save"])
    exports = [dict(e, path=p(e["path"])) for e in spec.get("exports", [])]
    base = p(spec["base"]) if spec.get("base") else None
    for out in [save] + [e["path"] for e in exports]:
        if base and same_file(out, base):
            sys.exit("refusing to write over the base drawing %s" % out)
        if os.path.exists(out) and not a.overwrite:
            sys.exit("%s exists (pass --overwrite to replace it)" % out)

    metric = spec.get("metric", True)
    th = spec.get("textHeight", 2.5 if metric else 0.125)
    named, created = {}, []
    s = Session()
    try:
        if base:
            s.tool("open", {"path": base})
        else:
            s.tool("new_drawing", {"metric": metric})
        for layer in spec.get("layers", []):
            s.ensure_layer(layer)
        for i, item in enumerate(spec.get("draw", [])):
            if item.get("layer"):
                s.ensure_layer({"name": item["layer"]}, current=True)
            if "script" in item:
                res = s.tool("script", {"text": item["script"]})
            else:
                params = resolve(item.get("params", {}), named)
                if item["cmd"] in TEXT_CMDS and "height" not in params:
                    params["height"] = th
                res = s.cmd(item["cmd"], params)
            handle = res.get("handle") if isinstance(res, dict) else None
            if item.get("as"):
                if not handle:
                    raise ToolError("draw[%d] %s returned no handle for \"as\"" % (i, item.get("cmd")))
                named[item["as"]] = handle
            created.append({"i": i, "cmd": item.get("cmd", "script"), "handle": handle,
                            "layer": item.get("layer")})
        if spec.get("titleBlock"):
            created.append({"titleBlock": s.title_block(spec["titleBlock"], th)})
        s.tool("save", {"path": save})
    except ToolError as e:
        print(json.dumps({"error": str(e), "created": created}))
        return 1
    finally:
        s.close()

    outputs = [save]
    for e in exports:
        try:
            convert(save, e["path"], view=e.get("view"), window=e.get("window"))
        except RuntimeError as err:
            print(json.dumps({"error": str(err)}))
            return 1
        outputs.append(e["path"])
    d = info(save)
    print(json.dumps({"created": created, "named": named, "outputs": outputs,
                      "info": {k: d.get(k) for k in ("counts", "extents", "blocks", "entityCount")},
                      "layers": [l["name"] for l in d.get("layers", [])]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
