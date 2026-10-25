#!/usr/bin/env python3
"""Run steps through one headless CADCraft session (cadcraft-cli mcp on stdio).

    cc_session.py STEPS.json|- [--root DIR]

STEPS is a JSON list; each step is one of
    {"new": {"metric": true}}                 new drawing (metric = mm; default imperial!)
    {"open": "in.dxf"}                        open a DXF/DWG (becomes the active drawing)
    {"cmd": "circle", "params": {...}}        any engine command with full JSON params
    {"line": "zoom e"}                        one AutoCAD-style command line
    {"script": "CIRCLE 0,0 5\\n"}             a multi-line .scr script (blank line = Enter)
    {"inspect": {"entities": false}}          drawing summary (inspect_drawing)
    {"query": {"type": "Insert", "layer": "TITLE"}}   entities with handles (query_entities)
    {"find_text": {"contains": "Rev"}}        texts, attributes, mtext, leaders
    {"save": "out.dxf"}                       save DXF/DWG; .pdf/.svg/.png exports instead
    {"render": "preview.png", "window": [[x0,y0],[x1,y1]]}   PNG preview (1600x1000)

"$N" anywhere in params becomes step N's "handle" (steps count from 0); "$N.key" its
result["key"] (e.g. "$4.handles" after a select/qselect; after a query, "$N.handles" is
the handles of the entities it returned). Relative paths become absolute and every
path must lie under --root (default: the current directory). An open input is never
saved over unless --allow-overwrite. Prints one JSON line per step; exits 1 at the first
error (the session and its unsaved changes are discarded).
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cclib import Session, ToolError, inside, same_file  # noqa: E402

REF = re.compile(r"^\$(\d+)(?:\.(\w+))?$")
PATH_KEYS = ("path", "file")


def resolve(value, results):
    if isinstance(value, str):
        m = REF.match(value)
        if not m:
            return value
        idx, key = int(m.group(1)), m.group(2) or "handle"
        res = results[idx] if idx < len(results) else None
        if isinstance(res, dict) and key == "handles" and key not in res \
                and isinstance(res.get("entities"), list):
            return [e["handle"] for e in res["entities"]]
        if not isinstance(res, dict) or key not in res:
            raise ToolError("ref %s: step %d has no %r" % (value, idx, key))
        return res[key]
    if isinstance(value, list):
        return [resolve(v, results) for v in value]
    if isinstance(value, dict):
        return {k: resolve(v, results) for k, v in value.items()}
    return value


class Runner:
    def __init__(self, root, allow_overwrite):
        self.root = os.path.realpath(root)
        self.allow_overwrite = allow_overwrite
        self.opened = []
        self.s = Session()

    def path(self, p):
        p = os.path.abspath(os.path.expanduser(p))
        if not inside(p, self.root):
            raise ToolError("path %s is outside --root %s" % (p, self.root))
        return p

    def guard_write(self, p):
        if not self.allow_overwrite and any(same_file(p, o) for o in self.opened):
            raise ToolError("refusing to overwrite the input %s (write a new path)" % p)
        return p

    def fix_paths(self, params):
        params = dict(params)
        for k in PATH_KEYS:
            if isinstance(params.get(k), str):
                params[k] = self.path(params[k])
        return params

    def step(self, st, results):
        s = self.s
        if "new" in st:
            return s.tool("new_drawing", st["new"] or {})
        if "open" in st:
            p = self.path(st["open"])
            self.opened.append(p)
            return s.tool("open", {"path": p})
        if "save" in st:
            return s.tool("save", {"path": self.guard_write(self.path(st["save"]))})
        if "render" in st:
            args = {"path": self.guard_write(self.path(st["render"]))}
            if st.get("window"):
                args["window"] = st["window"]
            s.tool("render", args)
            return {"path": args["path"]}
        if "cmd" in st:
            params = self.fix_paths(resolve(st.get("params", {}), results))
            if st["cmd"] in ("saveas", "export", "exportpdf", "plot", "wblock", "publish") \
                    and "path" in params:
                self.guard_write(params["path"])
            return s.cmd(st["cmd"], params)
        if "line" in st:
            return s.tool("command_line", {"text": st["line"]})
        if "script" in st:
            return s.tool("script", {"text": st["script"]})
        if "inspect" in st:
            return s.tool("inspect_drawing", st["inspect"] or {})
        if "query" in st:
            return s.tool("query_entities", st["query"] or {})
        if "find_text" in st:
            return s.tool("find_text", st["find_text"] or {})
        raise ToolError("unknown step: %s" % json.dumps(st))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("steps")
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--allow-overwrite", action="store_true")
    a = ap.parse_args()
    with (sys.stdin if a.steps == "-" else open(a.steps)) as f:
        steps = json.load(f)
    r = Runner(a.root, a.allow_overwrite)
    results = []
    try:
        for i, st in enumerate(steps):
            try:
                res = r.step(st, results)
            except ToolError as e:
                print(json.dumps({"step": i, "error": str(e)}))
                return 1
            results.append(res)
            print(json.dumps({"step": i, "result": res}))
    finally:
        r.s.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
