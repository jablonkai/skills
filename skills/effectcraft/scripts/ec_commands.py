#!/usr/bin/env python3
"""Filtered lookup in EffectCraft's command registry (about 743 commands in 0.20.0).

  ec_commands.py WORD…            commands whose id or label contains every word
  ec_commands.py --prefix keys.   every command under a prefix
  ec_commands.py --id layer.newText [--schema]   one command, its params (and JSON Schema)

Prints `id  label  params` lines. Use it instead of dumping `effectcraft-cli commands`.
"""
import argparse
import json
import sys

from eclib import run_cli


def registry():
    return json.loads(run_cli(["--empty", "exec", "--list", "--schemas", "--json"]).stdout)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("words", nargs="*")
    ap.add_argument("--prefix")
    ap.add_argument("--id")
    ap.add_argument("--schema", action="store_true", help="with --id: print the JSON Schema")
    ap.add_argument("--limit", type=int, default=40)
    a = ap.parse_args()
    if not (a.words or a.prefix or a.id):
        ap.error("give WORDs, --prefix or --id")

    cmds = registry()
    if a.id:
        hit = [c for c in cmds if c["id"] == a.id]
        if not hit:
            sys.exit("no command %s; try: ec_commands.py %s" % (a.id, a.id.split(".")[-1]))
        c = hit[0]
        print("%s  %s  %s" % (c["id"], c.get("label", ""), c.get("params") or "{}"))
        if a.schema:
            print(json.dumps(c.get("schema"), indent=2))
        return
    words = [w.lower() for w in a.words]
    hits = [c for c in cmds
            if (not a.prefix or c["id"].startswith(a.prefix))
            and all(w in (c["id"] + " " + c.get("label", "")).lower() for w in words)]
    for c in hits[:a.limit]:
        print("%-34s %-30s %s" % (c["id"], c.get("label", ""), c.get("params") or ""))
    if len(hits) > a.limit:
        print("… %d more; narrow the words or raise --limit" % (len(hits) - a.limit))


if __name__ == "__main__":
    main()
