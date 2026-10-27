#!/usr/bin/env python3
"""Run a PdfCraft tool script and print one line per step.

  pf_run.py STEPS.json [--root DIR] [--dry-run] [--full]

STEPS is the `run --script` format: [{"tool": "doc_open", "args": {...}}, ...]
("-" reads stdin). Differences from calling pdfcraft-cli directly:

- a step whose tool takes `doc` but omits it gets the id of the most recently
  opened or created document (ids are assigned 1, 2, 3… in script order);
  "doc": "@1", "@2"… names the first, second… document explicitly;
- relative paths in path/paths/out/out_dir/folder/file are made absolute against
  the current directory;
- OCR works (PDFCRAFT_MODELS is set to the app bundle);
- the exit status is 1 when any step failed or was skipped.

--full prints the whole JSON report instead of the summary.
"""

import argparse
import json
import os
import sys

import pflib

PATH_KEYS = {"path", "out", "out_dir", "folder", "file"}
LIST_PATH_KEYS = {"paths"}
SUMMARY_KEYS = ("doc", "pages", "path", "bytes", "marked", "applied", "marks_pending",
                "count", "recognized", "completed", "failed", "matches", "files")


def tool_takes_doc(tools):
    return {t["name"] for t in tools
            if "doc" in (t.get("input_schema") or {}).get("properties", {})}


def resolve(steps, takes_doc):
    opened = 0
    for i, step in enumerate(steps, 1):
        if "tool" not in step:
            pflib.die(f"step {i} has no \"tool\"")
        args = step.setdefault("args", {})
        for key in PATH_KEYS & args.keys():
            if isinstance(args[key], str):
                args[key] = os.path.abspath(args[key])
        for key in LIST_PATH_KEYS & args.keys():
            if isinstance(args[key], list):
                args[key] = [os.path.abspath(p) if isinstance(p, str) else p for p in args[key]]
        doc = args.get("doc")
        if isinstance(doc, str) and doc.startswith("@"):
            args["doc"] = int(doc[1:])
        elif doc is None and step["tool"] in takes_doc and step["tool"] not in pflib.OPENERS:
            if opened == 0:
                pflib.die(f"step {i} ({step['tool']}) needs a document; open or create one first")
            args["doc"] = opened
        if pflib.opens_doc(step):
            opened += 1
    return steps


def brief(result):
    r = pflib.first(result)
    if not isinstance(r, dict):
        return json.dumps(r)[:160]
    bits = []
    for k in SUMMARY_KEYS:
        if r.get(k) is not None:
            v = r[k]
            if isinstance(v, list):
                v = f"[{len(v)}]"
            bits.append(f"{k}={v}")
    if not bits:
        bits.append(json.dumps(r)[:160])
    return " ".join(bits)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("steps")
    ap.add_argument("--root", help="confine reads and writes to DIR (passed to pdfcraft-cli)")
    ap.add_argument("--dry-run", action="store_true", help="print the resolved steps and stop")
    ap.add_argument("--full", action="store_true", help="print the whole JSON report")
    a = ap.parse_args()

    raw = sys.stdin.read() if a.steps == "-" else open(a.steps).read()
    steps = json.loads(raw)
    if not isinstance(steps, list):
        pflib.die("the steps file must hold a JSON array")
    tools, _ = pflib.run_json(["tools"])
    steps = resolve(steps, tool_takes_doc(tools))

    if a.dry_run:
        print(json.dumps(steps, indent=2))
        return

    report = pflib.run_steps(steps, a.root)
    if a.full:
        print(json.dumps(report, indent=2))
    else:
        for s in report.get("steps", []):
            line = f"{s.get('step'):>3} {s.get('tool'):<24} {s.get('status'):<8}"
            if s.get("status") == "ok":
                line += brief(s.get("result"))
            elif s.get("error"):
                line += s["error"]
            print(line)
            result = pflib.first(s.get("result"))
            if isinstance(result, dict):
                for w in result.get("warnings") or []:
                    print(f"      warning: {w}")
    sys.exit(0 if report.get("ok") and not pflib.step_failures(report) else 1)


if __name__ == "__main__":
    main()
