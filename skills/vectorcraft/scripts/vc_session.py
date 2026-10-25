#!/usr/bin/env python3
"""Run steps through one headless VectorCraft session (vectorcraft-cli mcp --headless).

    vc_session.py STEPS.json|- [--root DIR | --read-root DIR --write-root DIR]

STEPS is a JSON list; each step is one of
    {"open": "in.svg"}                      open a file (becomes the active document)
    {"cmd": "text.setText", "params": {…}}  any engine command (vectorcraft-cli commands)
    {"batch": [{"id": …, "params": …}], "atomic": true}   command_batch ($N.id refs work)
    {"find": {"name"|"text"|"kind": …}}     print document.find matches
    {"inspect": {"depth": 3}}               print the layer tree (doc_inspect)
    {"export": {"path": …, "artboard": 0, "scale": 2, "outlineText": true}}
    {"save": "out.vectorcraft"}             save (the extension picks the format)
    {"preview": "out.png", "artboard": 0}   render a PNG preview (max side 1024)
    {"tool": "draw_shape", "args": {…}}     any other MCP tool

Strings "@name:Headline", "@text:Spring" or "@kind:Type" anywhere in params become the id
of the single matching object at that moment (an error when 0 or several match).
Relative paths become absolute. Roots default to the current directory; file access
outside them is refused. Prints one JSON line per step; exits 1 at the first error.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vclib import Session, ToolError, absolutize, resolve_refs  # noqa: E402


def run_step(s, step):
    if "open" in step:
        return s.tool("open_file", {"path": absolutize({"path": step["open"]})["path"]})
    if "save" in step:
        return s.tool("save_file", {"path": absolutize({"path": step["save"]})["path"]})
    if "export" in step:
        args = absolutize(resolve_refs(s, step["export"]))
        if "scale" in args:  # the export tool takes scale as an option on rasters
            args["scale"] = float(args["scale"])
        return s.tool("export", args)
    if "preview" in step:
        args = {"path": absolutize({"path": step["preview"]})["path"],
                "artboard": step.get("artboard", 0)}
        return s.cmd("document.export", dict(args, format="png"))
    if "cmd" in step:
        return s.cmd(step["cmd"], absolutize(resolve_refs(s, step.get("params", {}))))
    if "batch" in step:
        steps = [{"id": b["id"], "params": absolutize(resolve_refs(s, b.get("params", {})))}
                 for b in step["batch"]]
        return s.batch(steps, atomic=step.get("atomic", False))
    if "find" in step:
        return s.find(**step["find"])
    if "inspect" in step:
        return s.tool("doc_inspect", step["inspect"] or {})
    if "tool" in step:
        return s.tool(step["tool"], absolutize(resolve_refs(s, step.get("args", {}))))
    raise ToolError("unknown step: %s" % json.dumps(step))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("steps")
    ap.add_argument("--root")
    ap.add_argument("--read-root")
    ap.add_argument("--write-root")
    a = ap.parse_args()
    steps = json.load(sys.stdin if a.steps == "-" else open(a.steps))
    read_root = a.read_root or a.root or os.getcwd()
    write_root = a.write_root or a.root or os.getcwd()
    s = Session(read_root, write_root)
    try:
        for i, step in enumerate(steps):
            try:
                result = run_step(s, step)
            except ToolError as e:
                print(json.dumps({"step": i, "error": str(e)}))
                return 1
            print(json.dumps({"step": i, "result": result}))
    finally:
        s.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
