#!/usr/bin/env python3
"""Run steps through one headless FigCraft session (figcraft-cli mcp).

    fc_session.py STEPS.json|- [--root DIR | --read-root DIR --write-root DIR]

STEPS is a JSON list; each step is one of
    {"open": "in.fig"}                        open .figcraft/.fig/.json/.svg/image (active doc)
    {"cmd": "node.set", "params": {…}}        any engine command (fc_commands.py)
    {"batch": [{"command": …, "params": …}]}  one undo step; {"$step": n} = step n's id
    {"find": {"name"|"text"|"type": …}}       print matching layers (every page)
    {"inspect": {"depth": 4}}                 print the document (inspect_document)
    {"node": 12, "depth": 2}                  print one layer (get_node); "@name:…" works
    {"export": {"ids": [...], "path": …, "scale": 2, "bleed": "3mm", "cropMarks": true}}
    {"save": "out.figcraft"}                  save (.fig: experimental export copy)
    {"screenshot": "look.png", "ids": [...]}  render layers or the page to a PNG file
    {"tool": "set_properties", "args": {…}}   any other MCP tool

Strings "@name:Headline", "@text:Sign in" or "@type:COMPONENT" anywhere in params become
the id of the single matching layer at that moment (an error when 0 or several match;
"@name:Home/Headline" narrows by top-level frame). Relative paths become absolute.
Roots default to the current directory; file access outside them is refused. Prints one
JSON line per step; exits 1 at the first error.
"""
import argparse
import base64
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fclib import Session, ToolError, absolutize, resolve_refs  # noqa: E402


def abspath(p):
    return absolutize({"path": p})["path"]


def outpath(p):
    """Absolute output path with its folder created (FigCraft won't create it)."""
    p = abspath(p)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p


def run_step(s, step):
    if "open" in step:
        res = s.tool("open_file", {"path": abspath(step["open"])})
        # the full document comes along; keep the summary and the import warnings
        opened = (res or {}).get("opened") or {}
        frames = [{"id": c.get("id"), "name": c.get("name"), "type": c.get("type")}
                  for p in (res or {}).get("document", {}).get("pages", []) for c in p.get("children") or []]
        return {"summary": opened.get("summary"), "warnings": opened.get("warnings", []), "topLevel": frames}
    if "save" in step:
        return s.tool("save_file", {"path": outpath(step["save"])})
    if "export" in step:
        args = absolutize(resolve_refs(s, step["export"]))
        if "path" in args:
            outpath(args["path"])
        return s.tool("export", args)
    if "screenshot" in step:
        args = resolve_refs(s, {k: v for k, v in step.items() if k in ("ids", "maxSize", "scale")})
        res = s.tool("screenshot", args)
        path = outpath(step["screenshot"])
        with open(path, "wb") as fh:
            fh.write(base64.b64decode(res["images"][0]["data"]))
        return dict(res.get("result") or {}, path=path)
    if "cmd" in step:
        return s.cmd(step["cmd"], absolutize(resolve_refs(s, step.get("params", {}))))
    if "batch" in step:
        cmds = [{"command": b["command"], "params": absolutize(resolve_refs(s, b.get("params", {})))}
                for b in step["batch"]]
        return s.batch(cmds, step.get("label"))
    if "find" in step:
        return [{k: m[k] for k in ("id", "name", "type", "page", "parent")}
                for m in s.find(**step["find"])]
    if "inspect" in step:
        return s.tool("inspect_document", step["inspect"] or {})
    if "node" in step:
        return s.tool("get_node", {"id": resolve_refs(s, step["node"]), "depth": step.get("depth", 1)})
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
