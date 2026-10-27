#!/usr/bin/env python3
"""Run a FilmCraft step list in one headless session, with results passed between steps, then save.

    fc_run.py [--project IN.fcproj] --out OUT.fcproj [--overwrite] [--keep-going] STEPS

STEPS is a .json list or .jsonl file (or - for stdin) of {"id", "params", "as"?}. A step
with "as": "name" keeps its result; later params can use "$name.path" strings, e.g.
"$cut.placed[1][0]" (the 2nd placed clip's video id) or "$seq.sequence". A string that is
exactly one reference takes the referenced value's type (number, list, …).

Nothing is saved when a step fails (unless --keep-going). Saving goes to --out through
file.saveAs; --out must not exist (or be the input) without --overwrite. After saving it
prints the active sequence: tracks, clips (frames), transitions, markers, in/out.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fclib import Session, summary  # noqa: E402

REF = re.compile(r"\$([A-Za-z_][\w]*)((?:\.[A-Za-z_]\w*|\[\d+\])*)")


def load_steps(path):
    text = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
    stripped = text.lstrip()
    if stripped.startswith("["):
        return json.loads(stripped)
    steps = []
    for n, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            steps.append(json.loads(line))
        except json.JSONDecodeError as e:
            sys.exit(f"line {n}: not JSON ({e})")
    return steps


def lookup(saved, name, path):
    if name not in saved:
        raise KeyError(f"${name} is not defined by an earlier step's \"as\"")
    val = saved[name]
    for key in re.findall(r"\.(\w+)|\[(\d+)\]", path):
        val = val[key[0]] if key[0] else val[int(key[1])]
    return val


def resolve(obj, saved):
    if isinstance(obj, dict):
        return {k: resolve(v, saved) for k, v in obj.items()}
    if isinstance(obj, list):
        return [resolve(v, saved) for v in obj]
    if isinstance(obj, str) and "$" in obj:
        whole = REF.fullmatch(obj)
        if whole:
            return lookup(saved, whole.group(1), whole.group(2))
        return REF.sub(lambda m: str(lookup(saved, m.group(1), m.group(2))), obj)
    return obj


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", help="open this .fcproj first (default: a new empty project)")
    ap.add_argument("--out", required=True, help="save the project here (.fcproj)")
    ap.add_argument("--overwrite", action="store_true", help="allow --out to replace a file or the input")
    ap.add_argument("--keep-going", action="store_true", help="report failing steps, run the rest, and save")
    ap.add_argument("steps")
    a = ap.parse_args()

    out = os.path.abspath(a.out)
    if not out.endswith(".fcproj"):
        sys.exit("--out must end in .fcproj")
    if a.project and os.path.abspath(a.project) == out and not a.overwrite:
        sys.exit("--out is the input project; pass --overwrite to save over it, or pick a new name")
    if os.path.exists(out) and not a.overwrite:
        sys.exit(f"{a.out} exists; pass --overwrite or pick a new name")
    if a.project and not os.path.exists(a.project):
        sys.exit(f"{a.project} not found")

    steps = load_steps(a.steps)
    session = Session(os.path.abspath(a.project) if a.project else None)
    saved, failed = {}, 0
    try:
        for n, step in enumerate(steps, 1):
            cid = step.get("id")
            try:
                params = resolve(step.get("params") or {}, saved)
                if cid == "file.exportMedia":
                    params.setdefault("wait", True)  # async over MCP: unwaited jobs never write the file
                result = session.run(cid, params)
            except (RuntimeError, KeyError, IndexError, TypeError) as e:
                failed += 1
                print(f"FAIL {n} {cid}: {e}")
                if not a.keep_going:
                    print(f"nothing saved; fix step {n} and rerun the whole list")
                    sys.exit(1)
                continue
            if step.get("as"):
                saved[step["as"]] = result
            print(f"ok   {n} {cid}: {json.dumps(result, ensure_ascii=False)[:160]}")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        res = session.run("file.saveAs", {"path": out})
        print(f"saved {res.get('path', out) if isinstance(res, dict) else out}")
        summary(session.tool("sequence_inspect"))
    finally:
        session.close()
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
