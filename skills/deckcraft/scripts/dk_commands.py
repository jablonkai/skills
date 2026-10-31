#!/usr/bin/env python3
"""Filtered lookup in DeckCraft's command registry (330 commands in 0.13.1).

  dk_commands.py WORD…              commands whose id or label contains every word
  dk_commands.py --prefix slide.    every command under a prefix
  dk_commands.py --id file.export   one command spelled out (deckcraft-cli describe)

Prints `id — label: params` lines, cut to --width. Use it instead of reading the whole
`deckcraft-cli commands` list (about 35 KB).
"""
import argparse
import sys

from dklib import run_cli


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("words", nargs="*")
    ap.add_argument("--prefix")
    ap.add_argument("--id")
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--width", type=int, default=200, help="cut lines after N chars (0: never)")
    a = ap.parse_args()
    if not (a.words or a.prefix or a.id):
        ap.error("give WORDs, --prefix or --id")

    if a.id:
        proc = run_cli(["describe", a.id], check=False)
        if proc.returncode != 0:
            sys.exit("no command %s; try: dk_commands.py %s" % (a.id, a.id.split(".")[-1]))
        print(proc.stdout.rstrip())
        return
    lines = [l for l in run_cli(["commands"]).stdout.splitlines() if " — " in l]
    words = [w.lower() for w in a.words]
    hits = []
    for line in lines:
        cid, rest = line.split(" — ", 1)
        label = rest.split(":", 1)[0]
        if a.prefix and not cid.startswith(a.prefix):
            continue
        if all(w in (cid + " " + label).lower() for w in words):
            hits.append(line)
    for line in hits[:a.limit]:
        print(line if not a.width or len(line) <= a.width else line[:a.width] + "…")
    if len(hits) > a.limit:
        print("… %d more; narrow the words or raise --limit" % (len(hits) - a.limit))
    if not hits:
        print("no match; try fewer or shorter words")


if __name__ == "__main__":
    main()
