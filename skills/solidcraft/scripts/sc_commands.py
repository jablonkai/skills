#!/usr/bin/env python3
"""Filtered lookup in SolidCraft's command registry (493 commands in 0.25.1) and its bundled docs.

  sc_commands.py WORD…                 commands whose id or label contains every word
  sc_commands.py --prefix solid.       every command under a prefix
  sc_commands.py --id solid.hole       one command spelled out: full params, typed schema if any
  sc_commands.py --doc                 SolidCraft's bundled agent docs, listed
  sc_commands.py --doc solidcraft-modeling[/reference.md]   one of them

Prints `id — label: params` lines, cut to --width. Use it instead of reading the whole
`solidcraft-cli commands` output (about 400 KB of JSON).
"""
import argparse
import json
import sys

from sclib import Session, ToolError, run_cli

DOCS = ("solidcraft-modeling", "solidcraft-editing", "solidcraft-checking", "solidcraft-mechanisms")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("words", nargs="*")
    ap.add_argument("--prefix")
    ap.add_argument("--id")
    ap.add_argument("--doc", nargs="?", const="")
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--width", type=int, default=220, help="cut lines after N chars (0: never)")
    a = ap.parse_args()
    if not (a.words or a.prefix or a.id or a.doc is not None):
        ap.error("give WORDs, --prefix, --id or --doc")

    if a.doc is not None or a.id:
        s = Session()
        try:
            if a.id:
                print(json.dumps(s.tool("describe_command", {"id": a.id}), indent=2, ensure_ascii=False))
            elif not a.doc:
                for d in DOCS:
                    # an unknown file name is refused with the list of the skill's files
                    try:
                        files = s.tool("skill_reference", {"skill": d, "file": "?"})
                    except ToolError as e:
                        files = str(e)
                    print("%s: %s" % (d, str(files).split("Available files:")[-1].strip()))
            else:
                skill, _, f = a.doc.partition("/")
                print(s.tool("skill_reference", {"skill": skill, "file": f or "SKILL.md"}))
        except ToolError as e:
            sys.exit(str(e))
        finally:
            s.close()
        return

    cmds = json.loads(run_cli(["commands"]).stdout)
    words = [w.lower() for w in a.words]
    hits = []
    for c in cmds:
        if a.prefix and not c["id"].startswith(a.prefix):
            continue
        if all(w in (c["id"] + " " + (c.get("label") or "")).lower() for w in words):
            hits.append("%s — %s: %s" % (c["id"], c.get("label") or "", c.get("params") or "(no params)"))
    for line in hits[:a.limit]:
        print(line if not a.width or len(line) <= a.width else line[:a.width] + "…")
    if len(hits) > a.limit:
        print("… %d more; narrow the words or raise --limit" % (len(hits) - a.limit))
    if not hits:
        print("no match; try fewer or shorter words")


if __name__ == "__main__":
    main()
