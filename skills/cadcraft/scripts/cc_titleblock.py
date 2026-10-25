#!/usr/bin/env python3
"""Add an attributed title block to a drawing, or fill the attributes of an existing one.

    cc_titleblock.py add  IN OUT --at X,Y --size W,H [--name TB] [--layer TITLE]
                          [--height 3.5] TAG=VALUE[@DX,DY[,H]] ...
    cc_titleblock.py fill IN OUT [--block TB] TAG=VALUE ...
    cc_titleblock.py list IN

add:  draws a W x H frame at X,Y, one attribute per TAG (positions relative to the
      frame's lower-left corner; default: stacked from the top), makes block NAME from
      exactly those objects and inserts it with the values.
fill: sets the values on every reference of --block (or of every block that has the
      tags), via `attedit {handle, values}`; fails if a tag matches nothing.
list: block references with their attribute values (`eattext`).

OUT must differ from IN; existing OUT needs --overwrite. Prints JSON; exits 1 on error.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cclib import Session, ToolError, info, same_file  # noqa: E402


def parse_field(text, height):
    tag, _, rest = text.partition("=")
    value, _, pos = rest.partition("@")
    f = {"tag": tag.strip().upper(), "value": value}
    if pos:
        nums = [float(v) for v in pos.split(",")]
        f["at"] = nums[:2]
        if len(nums) > 2:
            f["height"] = nums[2]
    f.setdefault("height", height)
    return f


def inserts(s, block=None):
    res = s.tool("query_entities", {"type": "Insert", "limit": 10000})
    out = []
    for e in res.get("entities", []):
        g = e.get("geometry", {})
        name = g.get("name") or g.get("block")
        if block and name != block:
            continue
        out.append({"handle": e["handle"], "block": name,
                    "tags": [a.get("tag", "").upper() for a in g.get("attribs", [])]})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["add", "fill", "list"])
    ap.add_argument("input")
    ap.add_argument("output", nargs="?")
    ap.add_argument("fields", nargs="*")
    ap.add_argument("--at")
    ap.add_argument("--size")
    ap.add_argument("--name", default="TB")
    ap.add_argument("--block")
    ap.add_argument("--layer", default="TITLE")
    ap.add_argument("--height", type=float, default=3.5)
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_intermixed_args()
    src = os.path.abspath(a.input)

    s = Session()
    try:
        s.tool("open", {"path": src})
        if a.mode == "list":
            print(json.dumps(s.cmd("eattext", {}), indent=1))
            return 0
        if not a.output or not a.fields:
            sys.exit("%s needs OUT and at least one TAG=VALUE" % a.mode)
        out = os.path.abspath(a.output)
        if same_file(out, src):
            sys.exit("OUT must differ from IN (the input is never overwritten)")
        if os.path.exists(out) and not a.overwrite:
            sys.exit("%s exists (pass --overwrite)" % out)

        if a.mode == "add":
            if not (a.at and a.size):
                sys.exit("add needs --at X,Y and --size W,H")
            x, y = [float(v) for v in a.at.split(",")]
            w, h = [float(v) for v in a.size.split(",")]
            fields = [parse_field(f, a.height) for f in a.fields]
            row = h / (len(fields) + 1)
            for i, f in enumerate(fields):
                f.setdefault("at", [0.05 * w, h - row * (i + 1) - f["height"] / 2])
            res = s.title_block({"name": a.name, "at": [x, y], "size": [w, h],
                                 "layer": a.layer, "fields": fields}, a.height)
            result = {"insert": res}
        else:
            values = {}
            for f in a.fields:
                tag, _, value = f.partition("=")
                values[tag.strip().upper()] = value
            refs = [r for r in inserts(s, a.block) if set(values) & set(r["tags"])]
            if not refs:
                raise ToolError("no block reference%s carries any of %s"
                                % (" of " + a.block if a.block else "", sorted(values)))
            missing = set(values) - set(t for r in refs for t in r["tags"])
            if missing:
                raise ToolError("tags not found on any reference: %s" % sorted(missing))
            changed = []
            for r in refs:
                vals = {k: v for k, v in values.items() if k in r["tags"]}
                changed.append(dict(r, result=s.cmd("attedit", {"handle": r["handle"], "values": vals})))
            result = {"changed": changed}
        s.tool("save", {"path": out})
        result["attributes"] = s.cmd("eattext", {})
    except ToolError as e:
        print(json.dumps({"error": str(e)}))
        return 1
    finally:
        s.close()
    result["output"] = out
    result["counts"] = info(out).get("counts")
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
