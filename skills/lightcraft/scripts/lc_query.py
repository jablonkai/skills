#!/usr/bin/env python3
"""Read a LightCraft library back: photos, develop settings, and the command registry.

Usage:
  lc_query.py photos   (--library DIR | --demo) [--filter JSON] [--rating N [--op exactly]]
                       [--keyword K] [--flag pick|reject|none] [--text T]
                       [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--json]
  lc_query.py develop  (--library DIR | --demo) --ids 1,2|all [--keys light,white_balance]
                       [--diff] [--json]
  lc_query.py commands WORD...            registry ids whose id or label match every word

`photos` pages through catalog.query (all matches, not the first page) and refuses
filter keys LightCraft would silently ignore. `--rating N` means "at least N" unless
`--op exactly|atMost`. `develop` prints flattened develop.get values; `--diff` keeps
only the keys whose values differ between the photos. `commands` replaces the
missing `describe`: it prints each match's full params signature.
"""

import argparse
import json
import subprocess
import sys

import lclib


def build_filter(args):
    flt = json.loads(args.filter) if args.filter else {}
    if args.rating is not None:
        flt["rating"] = args.rating
        if args.op:
            flt["ratingOp"] = args.op
    for key, value in (("keyword", args.keyword), ("flag", args.flag), ("text", args.text),
                       ("dateFrom", args.date_from), ("dateTo", args.date_to)):
        if value is not None:
            flt[key] = value
    return flt


def cmd_photos(args):
    session = lclib.session_args(args.library, args.demo)
    flt = build_filter(args)
    photos = lclib.query_all(session, flt or None)
    if args.json:
        print(json.dumps({"filter": flt, "total": len(photos), "photos": photos}, indent=1))
        return 0
    print(f"{'id':>4}  {'file':<28} {'rating':>6}  {'flag':<6} {'label':<7} {'edited':<6} "
          f"{'captured':<19}  keywords")
    for p in photos:
        print(f"{p['id']:>4}  {p['fileName']:<28} {p['rating']:>6}  {p['flag']:<6} "
              f"{str(p.get('label') or '-'):<7} {str(p['edited']).lower():<6} "
              f"{p.get('captured') or '-':<19}  {', '.join(p.get('keywords') or [])}")
    print(f"total: {len(photos)}  filter: {json.dumps(flt)}")
    return 0


def cmd_develop(args):
    session = lclib.session_args(args.library, args.demo)
    ids = lclib.parse_ids(args.ids, session)
    settings = lclib.develop_of(session, ids)
    keys = sorted(set().union(*(s.keys() for s in settings.values())))
    if args.keys:
        wanted = [k.strip() for k in args.keys.split(",")]
        keys = [k for k in keys if any(k == w or k.startswith(w + ".") for w in wanted)]
    if args.diff:
        keys = [k for k in keys if len({json.dumps(settings[i].get(k)) for i in ids}) > 1]
    if args.json:
        print(json.dumps({str(i): {k: settings[i].get(k) for k in keys} for i in ids}, indent=1))
        return 0
    if not keys:
        print("no differing keys" if args.diff else "no matching keys")
        return 0
    width = max(len(k) for k in keys)
    print(f"{'key':<{width}}  " + "  ".join(f"{('#' + str(i)):>10}" for i in ids))
    for k in keys:
        cells = []
        for i in ids:
            v = settings[i].get(k)
            cells.append(f"{(round(v, 4) if isinstance(v, float) else v)!s:>10}")
        print(f"{k:<{width}}  " + "  ".join(cells))
    return 0


def cmd_commands(args):
    proc = subprocess.run([lclib.find_cli(), "commands", "--json"], capture_output=True, text=True)
    if proc.returncode != 0:
        lclib.die(proc.stderr.strip() or "lightcraft-cli commands failed", 1)
    words = [w.lower() for w in args.words]
    hits = [c for c in json.loads(proc.stdout)
            if all(w in (c["id"] + " " + c.get("label", "")).lower() for w in words)]
    for c in hits:
        print(f"{c['id']}  —  {c.get('label', '')}")
        print(f"    params: {c.get('params', '')}")
    print(f"{len(hits)} match(es)")
    return 0 if hits else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    for name in ("photos", "develop"):
        p = sub.add_parser(name)
        p.add_argument("--library")
        p.add_argument("--demo", action="store_true")
        p.add_argument("--json", action="store_true")
    photos = sub.choices["photos"]
    photos.add_argument("--filter")
    photos.add_argument("--rating", type=int)
    photos.add_argument("--op", choices=["atLeast", "exactly", "atMost"])
    photos.add_argument("--keyword")
    photos.add_argument("--flag", choices=["pick", "reject", "none"])
    photos.add_argument("--text")
    photos.add_argument("--from", dest="date_from")
    photos.add_argument("--to", dest="date_to")
    develop = sub.choices["develop"]
    develop.add_argument("--ids", required=True)
    develop.add_argument("--keys")
    develop.add_argument("--diff", action="store_true")
    commands = sub.add_parser("commands")
    commands.add_argument("words", nargs="+")

    args = ap.parse_args()
    return {"photos": cmd_photos, "develop": cmd_develop, "commands": cmd_commands}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
