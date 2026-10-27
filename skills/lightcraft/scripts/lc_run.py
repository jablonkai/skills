#!/usr/bin/env python3
"""Run a list of LightCraft commands in one headless lightcraft-cli process.

Usage:
  lc_run.py (--library DIR | --demo) [--import PATH]... [--keep-going] [--dry-run] STEPS|-

STEPS is a JSON array or JSON lines. Each step is one of:
  {"command": "photo.rate", "params": {"rating": 5, "ids": [1, 2]}}
  {"cmd": "develop.auto"}                                  (shorthand, no params)
  {"forEach": [1, 2, 3] | "all" | {filter}, "do": [steps]}

`forEach` expands to `library.select {ids: [n], active: n}` followed by the `do` steps,
once per photo. Use it for every command that acts on the ACTIVE photo only
(develop.auto, develop.adjust, develop.wb, develop.profile, ...): they ignore `ids`
and a multi-selection. "all" or a filter object is resolved with catalog.query
before the run (after any --import).

Anywhere in params, the string "@all" becomes the sorted list of every photo id in
the library (after any --import), e.g. {"ids": "@all"} for app.export or
develop.quickAdjust.

Prints one line per command (ok/FAIL, id, short result) and a JSON summary last.
Exit status: 0 when every command succeeded, 1 otherwise, 2 on usage errors.
"""

import argparse
import json
import sys

import lclib


def load_steps(source):
    text = sys.stdin.read() if source == "-" else open(source, encoding="utf-8").read()
    text = text.strip()
    if not text:
        lclib.die("no steps")
    if text.startswith("["):
        return json.loads(text)
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def normalise(step):
    if "cmd" in step and "command" not in step:
        step = {"command": step["cmd"], "params": step.get("params", {})}
    if "command" not in step and "method" not in step:
        lclib.die(f"step has no command: {json.dumps(step)}")
    return step


ALL = "@all"


def mentions_all(obj):
    if isinstance(obj, dict):
        return any(mentions_all(v) for v in obj.values())
    if isinstance(obj, list):
        return any(mentions_all(v) for v in obj)
    return obj == ALL


def needs_query(steps):
    return any(("forEach" in s and not isinstance(s["forEach"], list)) or mentions_all(s.get("params"))
               or mentions_all(s.get("do")) for s in steps)


def substitute(obj, ids):
    if isinstance(obj, dict):
        return {k: substitute(v, ids) for k, v in obj.items()}
    if isinstance(obj, list):
        return [substitute(v, ids) for v in obj]
    return list(ids) if obj == ALL else obj


def expand(steps, session):
    all_ids = sorted(p["id"] for p in lclib.query_all(session)) if needs_query(steps) else []
    steps = substitute(steps, all_ids)
    out = []
    for step in steps:
        if "forEach" not in step:
            out.append(normalise(step))
            continue
        target = step["forEach"]
        if isinstance(target, list):
            ids = [int(i) for i in target]
        elif target == "all":
            ids = all_ids
        elif isinstance(target, dict):
            ids = sorted(p["id"] for p in lclib.query_all(session, target))
        else:
            lclib.die(f"forEach must be a list of ids, 'all' or a filter: {target!r}")
        if not ids:
            lclib.die(f"forEach {json.dumps(target)} matched no photos")
        body = [normalise(s) for s in step.get("do", [])]
        if not body:
            lclib.die("forEach without a `do` list")
        for i in ids:
            out.append({"command": "library.select", "params": {"ids": [i], "active": i}})
            out.extend(body)
    return out


def short(reply):
    if not reply.get("ok"):
        return reply.get("error", "")
    text = json.dumps(reply.get("result"), separators=(",", ":"))
    return text if len(text) <= 140 else text[:137] + "..."


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("steps")
    ap.add_argument("--library")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--import", dest="imports", action="append", default=[])
    ap.add_argument("--keep-going", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="print the expanded steps, run nothing")
    args = ap.parse_args()

    steps = load_steps(args.steps)
    session = lclib.session_args(args.library, args.demo, args.imports)
    if args.imports and needs_query(steps):
        # Import first so "all"/filters see the new photos, then run without re-importing.
        if args.demo:
            lclib.die("--demo does not persist between processes; with --import use "
                      "forEach with explicit ids, or a --library")
        if args.dry_run:
            lclib.die("--dry-run cannot resolve forEach 'all'/filter before the import runs")
        lclib.call(session, "library.state")
        session = lclib.session_args(args.library, args.demo)
    expanded = expand(steps, session)

    if args.dry_run:
        for step in expanded:
            print(json.dumps(step))
        return 0

    code, replies = lclib.run_steps(session, expanded, args.keep_going)
    failed = []
    for reply in replies:
        ok = reply.get("ok")
        name = reply.get("command") or reply.get("method") or "?"
        print(f"{'ok  ' if ok else 'FAIL'} {name:<26} {short(reply)}")
        if not ok:
            failed.append({"command": name, "error": reply.get("error")})
    not_run = len(expanded) - len(replies)
    summary = {"steps": len(expanded), "ran": len(replies), "failed": failed}
    if not_run:
        summary["notRun"] = not_run
    print(json.dumps(summary))
    return 1 if failed or code != 0 else 0


if __name__ == "__main__":
    sys.exit(main())
