#!/usr/bin/env python3
"""Run a list of steps through one headless `photocraft-cli serve` session.

Usage:
  pc_session.py STEPS.json|STEPS.jsonl|- [--root DIR] [--read-root DIR] [--write-root DIR]
                [--keep-going]

STEPS is a JSON array or one JSON object per line. Each step is either
  {"cmd": "<engine command id>", "params": {...}}          (engine.execute)
  {"method": "doc.open|doc.save|doc.place|...", "params": {...}}

Any string "@layer:<name>" in params is replaced by that layer's numeric id, looked up
with doc.inspect right before the step (fails on a missing or duplicate name). Use it
instead of bare names: some commands ignore a name they can't resolve and edit the
active layer.

Prints one JSON line per step: {"step", "method", "ok", "result"|"error"}.
Stops at the first failed step (exit 1) unless --keep-going. Paths in params must
lie beneath the roots; both default to the current directory. Relative paths are
resolved against the root by PhotoCraft, so prefer absolute paths.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pclib import PcError, Session, die, layer_ids, layer_refs, substitute_refs, to_step  # noqa: E402


def read_steps(source):
    text = sys.stdin.read() if source == "-" else open(source).read()
    text = text.strip()
    if not text:
        return []
    if text.startswith("["):
        return json.loads(text)
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def shorten(result):
    """Keep base64 payloads out of the transcript."""
    if isinstance(result, dict) and isinstance(result.get("base64"), str):
        result = dict(result)
        result["base64"] = "<%d base64 chars; pass `path` to write a file>" % len(result["base64"])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("steps")
    parser.add_argument("--root", default=os.getcwd(), help="read and write root (default: cwd)")
    parser.add_argument("--read-root")
    parser.add_argument("--write-root")
    parser.add_argument("--keep-going", action="store_true")
    args = parser.parse_args()

    try:
        steps = read_steps(args.steps)
    except (OSError, ValueError) as exc:
        die("cannot read steps: %s" % exc)

    failed = 0
    try:
        with Session(args.read_root or args.root, args.write_root or args.root) as session:
            for index, step in enumerate(steps, 1):
                method, params = to_step(step)
                refs = layer_refs(params)
                if refs:
                    try:
                        ids = layer_ids(session.call("doc.inspect", {}), refs)
                    except PcError as exc:
                        print(json.dumps({"step": index, "method": step.get("cmd", method),
                                          "ok": False, "error": str(exc)}))
                        failed += 1
                        if args.keep_going:
                            continue
                        break
                    params = substitute_refs(params, ids)
                reply = session.request(method, params)
                row = {"step": index, "method": step.get("cmd", method), "ok": bool(reply.get("ok"))}
                if reply.get("ok"):
                    row["result"] = shorten(reply.get("result"))
                else:
                    row["error"] = reply.get("error")
                    failed += 1
                print(json.dumps(row))
                sys.stdout.flush()
                if failed and not args.keep_going:
                    break
    except PcError as exc:
        die(str(exc))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
