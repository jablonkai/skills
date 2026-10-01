#!/usr/bin/env python3
"""Run a shortcut with a timeout and checked outputs; print a JSON result.

Single run:
    python3 sc-run.py NAME [-i PATH ...] [-o PATH] [--output-type UTI] [--stdin TEXT]
Batch (one run per file, resumable):
    python3 sc-run.py NAME --batch IN_DIR --out OUT_DIR [--ext .png] [--glob '*.jpg' ...]
                      [--overwrite] [--fail-fast]

Common: --timeout SEC (default 60), --allow-empty (no output is not an error),
        --expect image|pdf|text (check every output file's content type).

NAME is a shortcut name or identifier. Text results go to "stdout" in the JSON unless -o is
given. With -o, a missing or empty output file is an error: Shortcuts silently writes
nothing for text output to an unknown extension (use .txt), and exits 0.

Exit codes: 0 ok, 1 the shortcut failed (stderr has its message), 2 bad arguments,
3 no output or wrong output type, 4 shortcut not found, 124 timeout, 130 interrupted. In a batch the first
non-zero item code wins; items already done are skipped on re-run unless --overwrite.
A batch output rejected by --expect is deleted, so it is retried rather than skipped.
"""
import argparse
import fnmatch
import json
import os
import signal
import subprocess
import sys
import time

EXIT_FAILED, EXIT_ARGS, EXIT_NO_OUTPUT, EXIT_NOT_FOUND, EXIT_TIMEOUT, EXIT_INT = 1, 2, 3, 4, 124, 130


def known_shortcuts():
    r = subprocess.run(["shortcuts", "list", "--show-identifiers"], capture_output=True, text=True)
    names, ids = set(), set()
    for line in r.stdout.splitlines():
        line = line.rstrip()
        if line.endswith(")") and " (" in line:
            name, ident = line[:-1].rsplit(" (", 1)
            names.add(name)
            ids.add(ident)
        elif line:
            names.add(line)
    return names, ids


def output_present(path):
    if not path or not os.path.exists(path):
        return False
    if os.path.isdir(path):
        return any(not f.startswith(".") for f in os.listdir(path))
    return os.path.getsize(path) > 0


IMAGE_MAGIC = (b"\x89PNG", b"\xff\xd8\xff", b"GIF8", b"II*\x00", b"MM\x00*", b"BM")


def kind_of(path):
    with open(path, "rb") as f:
        head = f.read(16)
    if head.startswith(IMAGE_MAGIC) or head[4:12] in (b"ftypheic", b"ftypheix", b"ftypmif1", b"ftypavif") \
            or (head.startswith(b"RIFF") and head[8:12] == b"WEBP"):
        return "image"
    if head.startswith(b"%PDF"):
        return "pdf"
    try:
        with open(path, encoding="utf-8") as f:
            f.read()
        return "text"
    except UnicodeDecodeError:
        return "binary"


def wrong_kinds(path, expect):
    files = [os.path.join(path, f) for f in sorted(os.listdir(path)) if not f.startswith(".")] \
        if os.path.isdir(path) else [path]
    return [f"{os.path.basename(f)}: {kind_of(f)}" for f in files if kind_of(f) != expect]


def run_once(name, inputs, output, output_type, stdin_text, timeout, allow_empty, expect=None):
    cmd = ["shortcuts", "run", name]
    for p in inputs:
        cmd += ["--input-path", p]
    if output:
        cmd += ["--output-path", output]
    if output_type:
        cmd += ["--output-type", output_type]
    result = {"shortcut": name, "inputs": inputs, "output": output}
    start = time.monotonic()
    # Own process group, so a timeout or Ctrl-C kills the CLI and anything it spawned.
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE if stdin_text is not None else subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        out, err = proc.communicate(stdin_text, timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.communicate()
        result.update(ok=False, exit=EXIT_TIMEOUT, seconds=round(time.monotonic() - start, 1),
                      error=f"timed out after {timeout}s: the shortcut is probably waiting for input "
                            "or a permission prompt that a CLI run cannot show")
        return result
    except KeyboardInterrupt:
        os.killpg(proc.pid, signal.SIGKILL)
        raise
    result.update(seconds=round(time.monotonic() - start, 1), stdout=out.rstrip("\n"), stderr=err.strip())
    if proc.returncode != 0:
        result.update(ok=False, exit=EXIT_FAILED, error=err.strip() or f"exit {proc.returncode}")
    elif output and not allow_empty and not output_present(output):
        result.update(ok=False, exit=EXIT_NO_OUTPUT,
                      error="shortcut exited 0 but wrote no output; check that it ends with an output "
                            "action and that the -o extension matches the result type (.txt for text)")
    elif output and expect and output_present(output) and wrong_kinds(output, expect):
        result.update(ok=False, exit=EXIT_NO_OUTPUT,
                      error=f"output is not {expect} ({', '.join(wrong_kinds(output, expect))}); a shortcut "
                            "given input of a type it does not accept still exits 0 and writes junk")
    elif not output and not allow_empty and not out.strip():
        result.update(ok=False, exit=EXIT_NO_OUTPUT, error="shortcut exited 0 but produced no output")
    else:
        result.update(ok=True, exit=0)
    return result


def batch(args):
    if not os.path.isdir(args.batch):
        print(f"sc-run: not a folder: {args.batch}", file=sys.stderr)
        return EXIT_ARGS, {}
    os.makedirs(args.out, exist_ok=True)
    patterns = args.glob or ["*"]
    files = sorted(f for f in os.listdir(args.batch)
                   if not f.startswith(".") and os.path.isfile(os.path.join(args.batch, f))
                   and any(fnmatch.fnmatch(f.lower(), p.lower()) for p in patterns))
    items, code = [], 0
    for f in files:
        stem, ext = os.path.splitext(f)
        dest = os.path.join(args.out, stem + (args.ext or ext))
        if not args.overwrite and output_present(dest) and not (args.expect and wrong_kinds(dest, args.expect)):
            items.append({"input": f, "output": dest, "ok": True, "exit": 0, "skipped": True})
            continue
        r = run_once(args.name, [os.path.join(args.batch, f)], dest, args.output_type, None,
                     args.timeout, args.allow_empty, args.expect)
        r["input"] = f
        items.append(r)
        if not r["ok"]:
            # Never leave a rejected (junk) output behind: a re-run would count it as done.
            if r["exit"] == EXIT_NO_OUTPUT and os.path.isfile(dest):
                os.remove(dest)
                r["removed_output"] = True
            code = code or r["exit"]
            if args.fail_fast:
                break
    summary = {"shortcut": args.name, "files": len(files), "ok": sum(i["ok"] for i in items),
               "failed": sum(not i["ok"] for i in items), "skipped": sum(bool(i.get("skipped")) for i in items),
               "items": items}
    return code, summary


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name")
    ap.add_argument("-i", "--input", action="append", default=[], help="input file (repeatable)")
    ap.add_argument("-o", "--output", help="output file, or a folder when the shortcut returns several items")
    ap.add_argument("--output-type", help="UTI, e.g. public.png or public.plain-text")
    ap.add_argument("--stdin", help="text passed to the shortcut as input on stdin")
    ap.add_argument("--batch", help="run once per file in this folder")
    ap.add_argument("--out", help="output folder for --batch")
    ap.add_argument("--ext", help="output extension for --batch (default: the input's)")
    ap.add_argument("--glob", action="append", help="--batch file filter, repeatable (default '*')")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--fail-fast", action="store_true")
    ap.add_argument("--timeout", type=float, default=60)
    ap.add_argument("--allow-empty", action="store_true")
    ap.add_argument("--expect", choices=["image", "pdf", "text"], help="required content type of -o files")
    args = ap.parse_args()

    if args.batch and (args.input or args.output or not args.out):
        ap.error("--batch needs --out and excludes -i/-o")
    names, ids = known_shortcuts()
    if args.name not in names and args.name not in ids:
        print(json.dumps({"shortcut": args.name, "ok": False, "exit": EXIT_NOT_FOUND,
                          "error": "no shortcut with this name or id; see `shortcuts list`"}, ensure_ascii=False))
        return EXIT_NOT_FOUND
    missing = [p for p in args.input if not os.path.exists(p)]
    if missing:
        print(json.dumps({"shortcut": args.name, "ok": False, "exit": EXIT_ARGS,
                          "error": f"input not found: {missing}"}, ensure_ascii=False))
        return EXIT_ARGS

    try:
        if args.batch:
            code, result = batch(args)
        else:
            result = run_once(args.name, args.input, args.output, args.output_type, args.stdin,
                              args.timeout, args.allow_empty, args.expect)
            code = result["exit"]
    except KeyboardInterrupt:
        print(json.dumps({"shortcut": args.name, "ok": False, "exit": EXIT_INT, "error": "interrupted"}))
        return EXIT_INT
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return code


if __name__ == "__main__":
    sys.exit(main())
