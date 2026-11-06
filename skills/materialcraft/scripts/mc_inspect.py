#!/usr/bin/env python3
"""Summarise a MaterialCraft package: graphs, nodes, wires, outputs, exposed inputs, presets, cook errors.

  mc_inspect.py IN.sbs [--graph N] [--params] [--no-cook] [--json-out FILE]

IN may be `sample` (the built-in brick wall). Without --graph the package's open graph is shown.
--params adds every node's parameter values (typed {t, v}), --no-cook skips the full cook.
Prints JSON; exits 1 when the cook reports errors or an output has nothing wired in.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mclib as m  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inp")
    ap.add_argument("--graph", type=int)
    ap.add_argument("--params", action="store_true")
    ap.add_argument("--no-cook", action="store_true")
    ap.add_argument("--json-out")
    a = ap.parse_args()

    whole = m.info(a.inp)
    g = whole["graph"] if a.graph is None else m.graph_of(a.inp, a.graph)
    bindings = {}
    nodes = []
    for n in g["nodes"]:
        row = {"id": n["id"], "def": n["def"], "label": n["label"]}
        if n.get("disabled"):
            row["disabled"] = True
        if a.params:
            row["params"] = n["params"]
            row["base"] = n["base"]
        nodes.append(row)
        for param, inp in n.get("bindings", {}).items():
            bindings.setdefault(inp, []).append("%d.%s" % (n["id"], param))
    out = {
        "cli": m.version(),
        "package": whole.get("package"),
        "graphs": whole.get("graphs"),
        "graph": {"index": g.get("index"), "name": g["name"], "size": g.get("size"), "format": g.get("format"),
                  "seed": g.get("seed")},
        "nodes": nodes,
        "wires": ["%d:%s -> %d:%s" % (c["from"], c["fromPort"], c["to"], c["toPort"]) for c in g["connections"]],
        "outputs": m.outputs(g),
        "exposed": [{"id": e["id"], "label": e.get("label"), "default": e.get("default"),
                     "min": e.get("min"), "max": e.get("max"), "bound_to": bindings.get(e["id"], [])}
                    for e in g.get("exposed", [])],
        "presets": g.get("presets", []),
        "graph_inputs": g.get("inputs", {}),
    }
    fails = []
    unbound = [e["id"] for e in out["exposed"] if not e["bound_to"]]
    if unbound:
        out["warnings"] = ["exposed inputs bound to nothing (changing them changes nothing): %s" % unbound]
    unwired = [o["identifier"] for o in out["outputs"] if o["source"] is None]
    if unwired:
        fails.append("outputs with nothing wired in: %s" % unwired)
    if not a.no_cook:
        args = ["cook", a.inp, "--full"]
        if a.graph is not None:
            args += ["--graph", str(a.graph)]
        cook = m.run_json(args)
        out["cook"] = {"ms": round(cook.get("ms", 0), 1), "errors": m.cook_errors(cook)}
        if out["cook"]["errors"]:
            fails.append("cook errors")
    out["ok"] = not fails
    out["failed"] = fails
    if a.json_out:
        with open(a.json_out, "w") as f:
            json.dump(out, f, indent=2)
    m.emit(out, ok=not fails)


if __name__ == "__main__":
    m.main_guard(main)
