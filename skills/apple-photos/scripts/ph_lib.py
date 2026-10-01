"""Shared helpers for the apple-photos scripts (Python 3.9+ stdlib only).

Reads go through the `osxphotos` CLI (a snapshot of the library database, Photos does
not need to run). Writes go through JXA against the running Photos app, which acts on
whatever library Photos has open, so every write helper checks that first.
"""
import json
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

SYSTEM_LIBRARY_HINT = Path.home() / "Pictures/Photos Library.photoslibrary"


def die(msg, code=1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def find_osxphotos():
    for cand in (os.environ.get("OSXPHOTOS"), shutil.which("osxphotos"),
                 str(Path.home() / ".local/bin/osxphotos"), "/opt/homebrew/bin/osxphotos"):
        if cand and os.access(cand, os.X_OK):
            return cand
    die("osxphotos not found. Install: uv tool install --python 3.13 osxphotos "
        "(or set OSXPHOTOS=/path/to/osxphotos)", 2)


def osxphotos(args, timeout=None):
    """Run osxphotos, return stdout. Its progress chatter goes to stderr and is dropped."""
    cmd = [find_osxphotos(), *args]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        die(f"timed out: {' '.join(cmd)}", 124)
    if res.returncode != 0:
        err = "\n".join(l for l in res.stderr.splitlines() if "UserQueryParser" not in l)
        die(f"osxphotos {' '.join(args[:2])} failed ({res.returncode}):\n{err[-2000:]}")
    return res.stdout


def library_args(library):
    return ["--library", str(Path(library).expanduser())] if library else []


def query_uuids(library, query_args, timeout=None):
    out = osxphotos(["query", *library_args(library), *query_args, "--quiet", "--print", "{uuid}"], timeout)
    return [l.strip() for l in out.splitlines() if l.strip()]


def open_library():
    """Path of the library the running Photos has open, or None if Photos is not running."""
    pid = subprocess.run(["pgrep", "-x", "Photos"], capture_output=True, text=True).stdout.split()
    if not pid:
        return None
    out = subprocess.run(["lsof", "-Fn", "-p", pid[0]], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("n") and line.endswith("/database/Photos.sqlite"):
            return str(Path(line[1:]).parent.parent)
    return None


def require_open_library(library):
    """Refuse to write unless Photos has exactly the library we queried open."""
    current = open_library()
    if current is None:
        die("Photos is not running. Open the target library in Photos first "
            "(open -a Photos /path/to/X.photoslibrary).", 3)
    if library:
        want = str(Path(library).expanduser().resolve())
        if Path(current).resolve() != Path(want):
            die(f"Photos has {current} open, not {want}. AppleScript writes go to the open "
                "library, so switch libraries first (quit Photos, open -a Photos LIBRARY).", 3)
    return current


def jxa(script, args=(), timeout=600):
    """Run a JXA script whose run(argv) returns a JSON string; return the parsed value."""
    proc = subprocess.Popen(["osascript", "-l", "JavaScript", "-", *args], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        out, err = proc.communicate(script, timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.send_signal(signal.SIGINT)
        proc.kill()
        die("Photos did not answer in time. A modal dialog may be open in Photos "
            "(check the window), or the batch is too large for one call.", 124)
    if proc.returncode != 0:
        if "-1743" in err:
            die("Automation permission denied: System Settings > Privacy & Security > "
                "Automation > allow your terminal to control Photos.", 4)
        die(f"osascript failed: {err.strip()[-1500:]}")
    return json.loads(out) if out.strip() else None


def split_query(argv):
    """Split argv at the first `--`: (own args, osxphotos query args)."""
    if "--" in argv:
        i = argv.index("--")
        return argv[:i], argv[i + 1:]
    return argv, []


def chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]
