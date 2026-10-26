#!/usr/bin/env python3
"""Run steps through one WordCraft session: headless, or in the running app.

    wc_session.py STEPS.json|- [--root DIR | --read-root DIR --write-root DIR] [--author NAME]
    wc_session.py STEPS.json|- --connect 127.0.0.1:PORT [--author NAME]   (live app, see wc_live.py)

STEPS is a JSON list; each step is one of
    {"new": "blank"}                         new document (blank|sample|letter|resume|report)
    {"open": "in.docx"}                      open a file
    {"cmd": "edit.replaceAll", "params": {…}}   any command (wc_commands.py to look ids up)
    {"batch": [{"command": …, "params": …}]}    several commands, stops at the first error
    {"type": "Hello"}                        type at the caret
    {"select": "late fee", "occurrence": 1}  select the n-th occurrence of some text
    {"inspect": true}                        print the document structure
    {"text": true}                           print the body text
    {"render": 1, "scale": 1}                render a page; the PNG is returned as base64
    {"save": "out.docx"}                     save (the extension picks the format)

Each step prints one JSON line; a failed step stops the run with exit 1. Headless file
access is confined to the roots (default: the current directory). With --connect the
steps act on the document open in the app; unsaved work there is the user's.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wclib import Session, ToolError, absolutize  # noqa: E402


def run_step(s, step):
    if "new" in step:
        return s.tool("new_document", {"template": step["new"] or "blank"})
    if "open" in step:
        return s.tool("open_document", {"path": absolutize({"path": step["open"]})["path"]})
    if "save" in step:
        return s.tool("save_document", {"path": absolutize({"path": step["save"]})["path"]})
    if "cmd" in step:
        return s.cmd(step["cmd"], absolutize(step.get("params", {})))
    if "batch" in step:
        return s.tool("batch", {"commands": absolutize(step["batch"]), "keepGoing": False})
    if "type" in step:
        return s.tool("type_text", {"text": step["type"]})
    if "select" in step:
        return s.tool("select_text", {"text": step["select"], "occurrence": step.get("occurrence", 1)})
    if "inspect" in step:
        return s.tool("inspect_document")
    if "text" in step:
        return s.tool("get_text")
    if "render" in step:
        return s.tool("render_page", {"page": step["render"], "scale": step.get("scale", 1)})
    raise ToolError("unknown step: %s" % json.dumps(step))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("steps")
    ap.add_argument("--root")
    ap.add_argument("--read-root")
    ap.add_argument("--write-root")
    ap.add_argument("--connect", help="HOST:PORT of a WordCraft app started with --control")
    ap.add_argument("--author", help="author of tracked changes and comments")
    a = ap.parse_args()
    steps = json.load(sys.stdin if a.steps == "-" else open(a.steps))
    s = Session(read_root=a.read_root or a.root or os.getcwd(),
                write_root=a.write_root or a.root or os.getcwd(),
                connect=a.connect, author=a.author)
    try:
        for i, step in enumerate(steps):
            try:
                result = run_step(s, step)
            except ToolError as e:
                print(json.dumps({"step": i, "error": str(e)}, ensure_ascii=False))
                return 1
            print(json.dumps({"step": i, "result": result}, ensure_ascii=False))
    finally:
        s.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
