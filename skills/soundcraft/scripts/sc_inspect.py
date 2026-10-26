#!/usr/bin/env python3
"""Compact read-outs of SoundCraft sessions, the command registry and plugin parameters.

Usage:
  sc_inspect.py session FILE [--json]
      Rate, depth, length, markers, busses, then per track: kind, format, volume, pan,
      mute/solo, inserts with their non-default params, sends, automation lanes and
      clips (id, start..end in m:ss.fff, gain, fades). Run it before editing a session.
  sc_inspect.py commands WORD...
      Registry ids matching every WORD, each with its params signature.
  sc_inspect.py plugin [ID...]
      Without ids, the built-in plugin list. With ids, each parameter's id, range,
      default, unit and choices: the values `mix.insert` params accept.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sclib import ScError, cli, die, fmt_time, inspect, result_lines  # noqa: E402


def plugin_table():
    out = cli("run", "--cmd", "engine.plugins")
    for cid, value in result_lines(out):
        if cid == "engine.plugins":
            return value
    raise ScError("engine.plugins returned nothing")


def show_session(a):
    doc = inspect(a.file)
    if a.json:
        print(json.dumps(doc, indent=2))
        return
    rate = doc["sample_rate"]
    defaults = {}
    used = {i["plugin"] for t in doc["tracks"] for i in t["inserts"]}
    if used:
        for p in plugin_table():
            if p["id"] in used:
                defaults[p["id"]] = {x["id"]: x["default"] for x in p["params"]}
    print("%s  %d Hz  %s  length %s  (%d samples)" % (
        doc["name"], rate, doc["bit_depth"], fmt_time(doc["length_samples"], rate),
        doc["length_samples"]))
    if doc.get("markers"):
        print("markers: " + ", ".join("%s@%s" % (m["name"], fmt_time(m["start"], rate))
                                      for m in doc["markers"]))
    if doc.get("busses"):
        print("busses: " + ", ".join(b["name"] for b in doc["busses"]))
    for t in doc["tracks"]:
        flags = [f for f in ("mute", "solo", "inactive", "hidden") if t.get(f)]
        print("\n[%s] %s  %s %s  vol %+.1f dB  pan %s  out %s%s" % (
            t["id"], t["name"], t["kind"], t["format"], t["volume_db"],
            "/".join("%.2f" % p for p in t["pan"]), t["output"],
            "  " + ",".join(flags) if flags else ""))
        for i in sorted(t["inserts"], key=lambda i: i["slot"]):
            d = defaults.get(i["plugin"], {})
            changed = {k: v for k, v in i["params"].items() if d.get(k) != v}
            print("  insert %s: %s%s%s" % (
                "abcdefghij"[i["slot"]], i["plugin"], " (bypassed)" if i["bypass"] else "",
                "  " + json.dumps(changed) if changed else ""))
        for s in t["sends"]:
            print("  send: " + json.dumps(s))
        for lane in t["automation"]:
            pts = lane["points"]
            print("  automation %s: %d points %s" % (
                lane["param"], len(pts),
                " ".join("%s=%g" % (fmt_time(p["at"], rate), p["value"]) for p in pts[:8])
                + (" ..." if len(pts) > 8 else "")))
        for c in t["clips"]:
            print("  clip %s %r %s..%s gain %+.1f dB fade in %.3fs out %.3fs%s" % (
                c["id"], c["name"], fmt_time(c["start"], rate), fmt_time(c["end"], rate),
                c["gain_db"], c["fade_in"] / float(rate), c["fade_out"] / float(rate),
                " muted" if c.get("muted") else ""))


def show_commands(a):
    words = [w.lower() for w in a.words]
    for row in cli("commands").splitlines():
        cid = row.split(" ", 1)[0]
        if cid and all(w in row.lower() for w in words):
            try:
                d = json.loads(cli("describe", cid))
                print("%s  %s" % (cid, d.get("params") or "{}"))
            except (ScError, ValueError):
                print(cid)


def show_plugin(a):
    table = plugin_table()
    if not a.ids:
        for p in table:
            print("%-18s %-22s %s%s" % (p["id"], p["name"], p["category"],
                                         " (instrument)" if p["instrument"] else ""))
        return
    known = {p["id"]: p for p in table}
    for pid in a.ids:
        if pid not in known:
            raise ScError("unknown plugin %r (see `sc_inspect.py plugin`)" % pid)
        p = known[pid]
        print("%s (%s, %s)" % (p["id"], p["name"], p["category"]))
        for x in p["params"]:
            extra = (" choices " + "|".join("%d=%s" % (i, c) for i, c in enumerate(x["choices"]))
                     if x["choices"] else "")
            print("  %-16s %g..%g  default %g  %s%s" % (
                x["id"], x["min"], x["max"], x["default"], x["unit"], extra))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="mode")
    s = sub.add_parser("session")
    s.add_argument("file")
    s.add_argument("--json", action="store_true")
    c = sub.add_parser("commands")
    c.add_argument("words", nargs="+")
    p = sub.add_parser("plugin")
    p.add_argument("ids", nargs="*")
    a = ap.parse_args()
    if not a.mode:
        ap.print_help()
        sys.exit(2)
    {"session": show_session, "commands": show_commands, "plugin": show_plugin}[a.mode](a)


if __name__ == "__main__":
    try:
        main()
    except ScError as exc:
        die(exc)
