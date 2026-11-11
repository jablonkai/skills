#!/usr/bin/env python3
"""Look up AniCraft engine commands without dumping the whole registry (225 in 0.2.0).

  ac_commands.py bone pose          ids/labels/params containing every word
  ac_commands.py --prefix motion.   one group
  ac_commands.py --id camera.set    one command, params in full
  ac_commands.py --groups           group names with counts

Prints `id [mutates] params` lines; params are the engine's own description.
"""
import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aclib  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("words", nargs="*")
    ap.add_argument("--prefix")
    ap.add_argument("--id")
    ap.add_argument("--groups", action="store_true")
    ap.add_argument("--width", type=int, default=240, help="truncate params (0: never)")
    args = ap.parse_args()

    cmds = json.loads(aclib.run_cli(["commands"]).stdout)
    if args.groups:
        counts = collections.Counter(c["id"].split(".")[0] for c in cmds)
        for group, n in sorted(counts.items()):
            print("%-10s %d" % (group, n))
        print("total      %d" % len(cmds))
        return
    if args.id:
        hit = [c for c in cmds if c["id"] == args.id]
        if not hit:
            near = [c["id"] for c in cmds if args.id.split(".")[-1] in c["id"]]
            sys.exit("no command %s%s" % (args.id, (" — near: " + ", ".join(near[:10])) if near else ""))
        print(json.dumps(hit[0], indent=1, ensure_ascii=False))
        return
    words = [w.lower() for w in args.words]
    shown = 0
    for c in cmds:
        params = c["params"] if isinstance(c["params"], str) else json.dumps(c["params"])
        hay = " ".join([c["id"], c.get("label") or "", c.get("menu") or "", params]).lower()
        if args.prefix and not c["id"].startswith(args.prefix):
            continue
        if not all(w in hay for w in words):
            continue
        if args.width and len(params) > args.width:
            params = params[:args.width] + "…"
        print("%s [%s] %s" % (c["id"], "mut" if c.get("mutates") else "ro", params))
        shown += 1
    if not shown:
        sys.exit("no command matches")


if __name__ == "__main__":
    main()
