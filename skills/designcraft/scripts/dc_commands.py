#!/usr/bin/env python3
"""Filtered lookup in DesignCraft's command registry (537 commands in 0.13.0).

  dc_commands.py WORD…              commands whose id, label or menu path contains every word
  dc_commands.py --prefix style.    every command under a prefix
  dc_commands.py --id data.merge    one command with its full params signature

Prints `id  label  params` lines. Use it instead of dumping `designcraft-cli commands`
(about 180 KB of JSON).
"""
import argparse
import json
import sys

from dclib import run_cli


def registry():
    return json.loads(run_cli(["commands"]).stdout)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("words", nargs="*")
    ap.add_argument("--prefix")
    ap.add_argument("--id")
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--width", type=int, default=160, help="cut params after N chars (0: never)")
    a = ap.parse_args()
    if not (a.words or a.prefix or a.id):
        ap.error("give WORDs, --prefix or --id")

    cmds = registry()
    if a.id:
        hit = [c for c in cmds if c["id"] == a.id]
        if not hit:
            sys.exit("no command %s; try: dc_commands.py %s" % (a.id, a.id.split(".")[-1]))
        c = hit[0]
        print("%s  %s  [%s]\n%s" % (c["id"], c.get("label", ""), " › ".join(c.get("menu") or []),
                                     c.get("params") or "{}"))
        return
    words = [w.lower() for w in a.words]

    def haystack(c):
        return " ".join([c["id"], c.get("label", "")] + (c.get("menu") or [])).lower()

    hits = [c for c in cmds if (not a.prefix or c["id"].startswith(a.prefix))
            and all(w in haystack(c) for w in words)]
    for c in hits[:a.limit]:
        params = c.get("params") or ""
        if a.width and len(params) > a.width:
            params = params[:a.width] + "…"
        print("%-30s %-28s %s" % (c["id"], c.get("label", ""), params))
    if len(hits) > a.limit:
        print("… %d more; narrow the words or raise --limit" % (len(hits) - a.limit))


if __name__ == "__main__":
    main()
