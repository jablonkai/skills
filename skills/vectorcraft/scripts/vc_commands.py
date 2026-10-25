#!/usr/bin/env python3
"""Filtered lookup over the VectorCraft command catalogue (vectorcraft-cli commands).

    vc_commands.py WORD...          ids whose id or label contains every word, with params
    vc_commands.py --prefix text.   every id under a namespace
    vc_commands.py --id text.setText   one command in full

The catalogue holds ~811 commands; never print all of it into context.
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vclib import cli  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("words", nargs="*")
    ap.add_argument("--prefix")
    ap.add_argument("--id")
    ap.add_argument("--width", type=int, default=300, help="truncate params to N chars (0: full)")
    a = ap.parse_args()
    cmds = json.loads(subprocess.run([cli(), "commands"], capture_output=True, text=True, check=True).stdout)
    hits = []
    for c in cmds:
        hay = (c["id"] + " " + c.get("label", "")).lower()
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
        params = c.get("params", "")
        if width and len(params) > width:
            params = params[:width] + "…"
        print("%s  [%s]\n    %s" % (c["id"], " › ".join(c.get("menu", [])) or c.get("label", ""), params))
    if len(hits) > 40:
        print("(%d matches: add a word or --prefix)" % len(hits))
    return 0


if __name__ == "__main__":
    sys.exit(main())
