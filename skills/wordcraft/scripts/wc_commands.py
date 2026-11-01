#!/usr/bin/env python3
"""Filtered lookup over the WordCraft command registry (wordcraft-cli commands --json).

    wc_commands.py WORD...            ids whose id, label or ribbon location has every word
    wc_commands.py --prefix review.   every id under a namespace
    wc_commands.py --id edit.replaceAll   one command in full

The registry holds ~648 commands in 0.14.0, and there is no `describe` subcommand:
this is the lookup. Never print all of it into context.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wclib import run_cli  # noqa: E402


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
        hay = " ".join((c["id"], c.get("label", ""), c.get("location", ""))).lower()
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
    for c in hits[:60]:
        params = c.get("params", "")
        if width and len(params) > width:
            params = params[:width] + "…"
        flag = "" if c.get("mutates") else "  (read-only)"
        print("%s  [%s › %s]%s\n    %s" % (c["id"], c.get("location", ""), c.get("label", ""), flag, params))
    if len(hits) > 60:
        print("(%d matches, first 60 shown: add a word or --prefix)" % len(hits))
    return 0


if __name__ == "__main__":
    sys.exit(main())
