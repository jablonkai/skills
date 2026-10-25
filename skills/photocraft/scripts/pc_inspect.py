#!/usr/bin/env python3
"""Inspect PhotoCraft documents and the engine command registry.

Usage:
  pc_inspect.py layers FILE [--json]
      Size, mode, depth, layer comps, variables, then the layer tree (top first):
      id, kind, visibility, name, bounds [x, y, w, h], text and effects.
  pc_inspect.py ids FILE NAME...
      {"name": id} for the named layers; fails on a missing or duplicate name. Ids
      are stable for one file on disk, so they are safe for `photocraft-cli run`
      on that same file (not across a save and re-open).
  pc_inspect.py commands FILTER... [--exact]
      Every command whose id contains each FILTER (case-insensitive), with its
      full params signature. --exact prints only the command whose id is FILTER.
"""

import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pclib import PcError, cli_path, die, info, layer_ids, walk  # noqa: E402


def cmd_layers(args):
    doc = info(args.file)
    if args.json:
        print(json.dumps(doc, indent=2))
        return
    print("%s  %dx%d  %s  %s-bit" % (
        doc.get("name") or args.file, doc["width"], doc["height"], doc.get("mode"), doc.get("depth")))
    comps = doc.get("layerComps") or []
    if comps:
        print("layer comps: " + ", ".join("%s (id %s)" % (c["name"], c["id"]) for c in comps))
    variables = doc.get("variables") or {}
    if variables.get("defs") or variables.get("dataSets"):
        print("variables: %d defs, %d data sets" % (
            len(variables.get("defs") or []), len(variables.get("dataSets") or [])))
    for depth, layer in walk(doc.get("layers") or []):
        bits = ["%4s" % layer.get("id"), "%-13s" % layer.get("kind"),
                "on " if layer.get("visible") else "off",
                "  " * depth + json.dumps(layer.get("name"), ensure_ascii=False),
                str(layer.get("bounds"))]
        text = layer.get("text")
        if text:
            bits.append("text=%s (%s %gpt)" % (
                json.dumps(text.get("text"), ensure_ascii=False), text.get("font"), text.get("sizePt") or 0))
        effects = (layer.get("effects") or {}).get("items") or []
        if effects:
            bits.append("fx=" + ",".join(e.get("kind", "?") for e in effects))
        if layer.get("opacity") not in (None, 1, 1.0):
            bits.append("opacity=%g" % layer["opacity"])
        print("  ".join(bits))


def cmd_ids(args):
    print(json.dumps(layer_ids(info(args.file), args.names), ensure_ascii=False))


def cmd_commands(args):
    proc = subprocess.run([cli_path(), "commands", "--json"],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if proc.returncode != 0:
        die(proc.stderr.strip())
    rows = json.loads(proc.stdout)
    needles = [f.lower() for f in args.filter]
    hits = 0
    for row in rows:
        cid = row["id"]
        if args.exact:
            if cid != args.filter[0]:
                continue
        elif not all(n in cid.lower() for n in needles):
            continue
        hits += 1
        menu = " > ".join(row.get("menu") or [])
        print("%s  [%s]%s" % (cid, row.get("label", ""), "  (" + menu + ")" if menu else ""))
        print("    params: %s" % (row.get("params") or "{}"))
    if not hits:
        die("no command matches %s; try a shorter filter" % " ".join(args.filter))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="action")
    p_layers = sub.add_parser("layers")
    p_layers.add_argument("file")
    p_layers.add_argument("--json", action="store_true")
    p_ids = sub.add_parser("ids")
    p_ids.add_argument("file")
    p_ids.add_argument("names", nargs="+")
    p_cmds = sub.add_parser("commands")
    p_cmds.add_argument("filter", nargs="+")
    p_cmds.add_argument("--exact", action="store_true")
    args = parser.parse_args()
    try:
        if args.action == "layers":
            cmd_layers(args)
        elif args.action == "ids":
            cmd_ids(args)
        elif args.action == "commands":
            cmd_commands(args)
        else:
            parser.print_help()
            sys.exit(2)
    except PcError as exc:
        die(str(exc))


if __name__ == "__main__":
    main()
