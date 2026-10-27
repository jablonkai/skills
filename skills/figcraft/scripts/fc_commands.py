#!/usr/bin/env python3
"""Filtered lookup over the FigCraft command registry (figcraft-cli commands --json).

    fc_commands.py WORD...            ids whose id or label contains every word, with params
    fc_commands.py --prefix style.    every id under a namespace
    fc_commands.py --id node.set      one command in full

The registry holds ~600 commands; never print all of it into context. `*` marks a
command that changes the document (one undo step).
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fclib import run_cli  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("words", nargs="*")
    ap.add_argument("--prefix")
    ap.add_argument("--id")
    ap.add_argument("--width", type=int, default=300, help="truncate params to N chars (0: full)")
    a = ap.parse_args()
    cmds = json.loads(run_cli(["commands", "--json"]).stdout)
    hits = []
    for c in cmds:
        hay = (c["id"] + " " + (c.get("label") or "")).lower()
        if a.id and c["id"] != a.id:
            continue
        if a.prefix and not c["id"].startswith(a.prefix):
            continue
        if any(w.lower() not in hay for w in a.words):
            continue
        hits.append(c)
    if not hits:
        print("no match")
        return 1
    width = 0 if a.id else a.width
    for c in hits:
        params = c.get("params") or ""
        if width and len(params) > width:
            params = params[:width] + "…"
        print("%s%s  [%s]\n    %s" % (c["id"], "*" if c.get("undoable") else "", c.get("label") or "", params))
    if len(hits) > 40:
        print("(%d matches: add a word or --prefix)" % len(hits))
    return 0


if __name__ == "__main__":
    sys.exit(main())
