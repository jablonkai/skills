"""Shared helpers for the lightcraft skill scripts (standard library only).

Finds lightcraft-cli, runs `lightcraft-cli run` with a list of steps and parses the
one-JSON-line-per-command replies, pages through catalog.query and flattens develop
settings for comparison.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

# Filter keys catalog.query / library.filter understand in 0.17.0 (library.state's
# `filter` object). Unknown keys are ignored silently by LightCraft, which turns a
# typo into "every photo", so the scripts refuse them instead.
FILTER_KEYS = {
    "album", "camera", "date", "dateFrom", "dateTo", "deleted", "edited", "flag",
    "folder", "imported", "importedFrom", "keyword", "kind", "label", "lens",
    "libraryFolder", "merged", "person", "rating", "ratingOp", "subfolders", "text",
}

PAGE = 500


def die(msg, code=2):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def find_cli():
    env = os.environ.get("LIGHTCRAFT_CLI")
    if env:
        return env
    found = shutil.which("lightcraft-cli")
    if found:
        return found
    fallback = os.path.expanduser("~/.local/bin/lightcraft-cli")
    if os.path.exists(fallback):
        return fallback
    die("lightcraft-cli not found (PATH, ~/.local/bin, or set LIGHTCRAFT_CLI)")


def session_args(library=None, demo=False, imports=()):
    if library and demo:
        die("pass --library or --demo, not both")
    if not library and not demo:
        die("pass --library DIR (or --demo for the throwaway demo library)")
    args = ["--demo"] if demo else ["--library", os.path.abspath(os.path.expanduser(library))]
    for path in imports:
        args += ["--import", os.path.abspath(os.path.expanduser(path))]
    return args


def run_steps(session, steps, keep_going=False):
    """Run steps ({"command", "params"} dicts) in ONE lightcraft-cli process.

    One process matters: the develop clipboard and other in-memory state do not
    survive between `run` invocations. Returns (exit_code, [reply dicts]).
    """
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as fh:
        for step in steps:
            fh.write(json.dumps(step) + "\n")
        script = fh.name
    cmd = [find_cli(), "run", *session, "--script", script]
    if keep_going:
        cmd.append("--keep-going")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    finally:
        os.unlink(script)
    replies = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                replies.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    if proc.returncode != 0 and not replies:
        die(proc.stderr.strip() or f"lightcraft-cli exited {proc.returncode}", proc.returncode)
    return proc.returncode, replies


def call(session, command, params=None):
    """Run one command and return its result, exiting on failure."""
    code, replies = run_steps(session, [{"command": command, "params": params or {}}])
    if not replies or not replies[-1].get("ok"):
        err = replies[-1].get("error") if replies else "no reply"
        die(f"{command}: {err}", 1)
    return replies[-1].get("result")


def check_filter(flt):
    unknown = sorted(set(flt) - FILTER_KEYS)
    if unknown:
        die(f"unknown filter key(s) {unknown}; LightCraft would ignore them and match "
            f"every photo. Known: {sorted(FILTER_KEYS)}")


def query_all(session, flt=None, sort=None):
    """Every photo matching `flt`, paging through catalog.query."""
    if flt:
        check_filter(flt)
    photos, offset = [], 0
    while True:
        params = {"offset": offset, "limit": PAGE}
        if flt:
            params["filter"] = flt
        if sort:
            params["sort"] = sort
        result = call(session, "catalog.query", params)
        batch = result.get("photos", [])
        photos += batch
        offset += len(batch)
        if not batch or offset >= result.get("total", 0):
            return photos


def flatten(obj, prefix=""):
    out = {}
    if isinstance(obj, dict):
        for key, value in obj.items():
            out.update(flatten(value, f"{prefix}.{key}" if prefix else key))
    else:
        out[prefix] = obj
    return out


def develop_of(session, ids):
    """{id: flattened develop settings} for the given photo ids, in one process."""
    steps = [{"command": "develop.get", "params": {"id": i}} for i in ids]
    code, replies = run_steps(session, steps)
    out = {}
    for i, reply in zip(ids, replies):
        if not reply.get("ok"):
            die(f"develop.get id={i}: {reply.get('error')}", 1)
        out[i] = flatten(reply.get("result") or {})
    if len(out) != len(ids):
        die("develop.get did not answer for every id", 1)
    return out


def parse_ids(text, session=None):
    """'1,2,5' or 'all' (needs a session) -> [int]."""
    if text == "all":
        return sorted(p["id"] for p in query_all(session))
    try:
        return [int(x) for x in text.split(",") if x.strip()]
    except ValueError:
        die(f"--ids must be comma-separated integers or 'all', got {text!r}")
