"""Shared helpers for the musescore skill scripts.

Locates the MuseScore Studio 4 CLI, runs it with a timeout, and judges a run by
the files it was asked to write rather than by its exit status: mscore 4.x can
abort with SIGABRT (rc 134) while shutting down *after* writing every output,
and some modes (-P, unsupported formats) exit having written nothing.
"""

import glob
import json
import os
import shutil
import subprocess
import time

APP_CANDIDATES = [
    "/Applications/MuseScore 4.app",
    "/Applications/MuseScore Studio 4.app",
    "/Applications/MuseScore Studio.app",
    os.path.expanduser("~/Applications/MuseScore 4.app"),
    os.path.expanduser("~/Applications/MuseScore Studio 4.app"),
]

# Formats MuseScore paginates: "-o out.png" writes out-1.png, out-2.png, ...
PAGED = {".png", ".svg"}


class MuseScoreError(RuntimeError):
    pass


def find_mscore():
    env = os.environ.get("MSCORE_BIN")
    if env:
        if os.access(env, os.X_OK):
            return env
        raise MuseScoreError(f"MSCORE_BIN={env} is not executable")
    for app in APP_CANDIDATES + sorted(glob.glob("/Applications/MuseScore*.app")):
        exe = os.path.join(app, "Contents", "MacOS", "mscore")
        if os.access(exe, os.X_OK):
            return exe
    for name in ("mscore4portable", "mscore4", "musescore4", "mscore", "musescore"):
        exe = shutil.which(name)
        if exe:
            return exe
    raise MuseScoreError(
        "MuseScore Studio 4 not found: install it (Muse Hub or musescore.org) or set MSCORE_BIN"
    )


def expected_files(path):
    """Files that '-o path' produces: page-numbered for PNG/SVG, else the path itself."""
    stem, ext = os.path.splitext(path)
    if ext.lower() in PAGED:
        return sorted(glob.glob(glob.escape(stem) + "-[0-9]*" + ext))
    return [path] if os.path.exists(path) else []


def fresh_outputs(path, since):
    """Outputs of '-o path' that exist, are non-empty and were written after `since`."""
    return [f for f in expected_files(path) if os.path.getsize(f) > 0 and os.path.getmtime(f) >= since - 1]


def run(args, timeout=300, capture=True):
    """Run mscore with args. Returns (returncode, stdout, stderr); rc -9 means timed out."""
    cmd = [find_mscore()] + list(args)
    try:
        p = subprocess.run(cmd, capture_output=capture, text=True, timeout=timeout)
        return p.returncode, p.stdout or "", p.stderr or ""
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        return -9, out, f"timed out after {timeout}s"


def convert(src, dst, extra=(), timeout=300):
    """Single '-o' conversion; returns the list of files written. Raises on failure."""
    for f in expected_files(dst) if os.path.splitext(dst)[1].lower() in PAGED else []:
        os.remove(f)  # stale pages from an earlier run would otherwise count as output
    start = time.time()
    rc, _, err = run(list(extra) + ["-o", dst, src], timeout=timeout)
    files = fresh_outputs(dst, start)
    if not files:
        raise MuseScoreError(f"no output for {dst} (mscore rc={rc}) {tail(err)}")
    return files


def run_job(entries, job_path, timeout, extra=()):
    """Run a '-j' job file. entries: [{"in": src, "out": [dst, ...]}]. Returns rc.

    Plain "name.png"/"name.svg" outputs come out page-numbered; the [prefix, suffix]
    array form some docs show writes nothing in 4.x, so don't use it.
    """
    with open(job_path, "w", encoding="utf-8") as fh:
        json.dump(entries, fh, indent=1, ensure_ascii=False)
    rc, _, _ = run(list(extra) + ["-j", job_path], timeout=timeout)
    return rc


def json_from_stdout(args, timeout=300):
    """Run an mscore mode that prints JSON (--score-meta, --score-parts-pdf, ...)."""
    rc, out, err = run(args, timeout=timeout)
    start = out.find("{")
    if start < 0:
        raise MuseScoreError(f"no JSON from mscore {' '.join(args[:1])} (rc={rc}) {tail(err)}")
    try:
        return json.JSONDecoder().raw_decode(out[start:])[0]
    except json.JSONDecodeError as e:
        raise MuseScoreError(f"unparseable JSON from mscore (rc={rc}): {e}") from e


def score_meta(path, timeout=120):
    data = json_from_stdout(["--score-meta", path], timeout=timeout)
    return data.get("metadata", data)


def tail(text, n=3):
    lines = [ln for ln in (text or "").strip().splitlines() if ln.strip()]
    return " | ".join(lines[-n:])


def safe_name(name):
    keep = "".join(c if c.isalnum() or c in " -_.()" else "_" for c in name).strip()
    return keep or "part"
