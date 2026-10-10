"""Shared helpers for the calibre skill scripts (run on calibre's Python via
`calibre.sh py`). Exit codes: 2 usage, 3 input missing/unreadable, 4 verification
failed, 5 calibre error, 6 library locked by the GUI / calibre-server."""
import json
import os
import subprocess
import sys

BIN = os.environ.get("CALIBRE_BIN", "/Applications/calibre.app/Contents/MacOS")
LOCK_MSG = "Another calibre program"


def emit(obj, code=0):
    print(json.dumps(obj, indent=1, ensure_ascii=False, default=str))
    sys.stdout.flush()
    os._exit(code)


def fail(code, msg, **extra):
    emit(dict(ok=False, error=msg, **extra), code)


def tool(name, *args, check=True):
    """Run a calibre CLI tool, return (returncode, stdout, stderr)."""
    env = dict(os.environ, CALIBRE_OVERRIDE_LANG="en")
    p = subprocess.run([os.path.join(BIN, name), *map(str, args)], capture_output=True,
                       text=True, env=env)
    if check and p.returncode != 0:
        fail(5, f"{name} failed ({p.returncode})", stderr=(p.stderr or p.stdout)[-2000:])
    return p.returncode, p.stdout, p.stderr


def calibredb(library, *args, check=True):
    """calibredb against a library path or Content server URL. A lock refusal exits 6,
    even for reads, which calibredb itself reports with exit status 0."""
    rc, out, err = tool("calibredb", "--with-library", library, *args, check=False)
    if LOCK_MSG in out + err:
        fail(6, "library is open in the calibre GUI or calibre-server; close it, or pass "
                "the Content server URL (bash calibre.sh lock shows it) as --library",
             library=library)
    if library.startswith("http") and rc != 0 and "Forbidden" in out + err:
        fail(6, "the calibre Content server refused the write (Forbidden): local writes are "
                "off. Nothing was changed. Ask the user to close calibre, or to enable "
                "Preferences > Sharing over the net > Advanced > 'Allow un-authenticated local "
                "connections to make changes' (calibre-server: --enable-local-write), or to "
                "give --username/--password of a user with write access.", library=library)
    if check and rc != 0:
        fail(5, f"calibredb {args[0]} failed ({rc})", stderr=(err or out)[-2000:])
    return rc, out, err


def default_library():
    from calibre.utils.config import prefs
    return prefs["library_path"]


def read_meta(path):
    """Metadata of an e-book file as a plain dict (calibre's own reader)."""
    from calibre.ebooks.metadata.meta import get_metadata
    ext = os.path.splitext(path)[1][1:].lower()
    with open(path, "rb") as f:
        mi = get_metadata(f, ext)
    return {
        "title": mi.title, "authors": list(mi.authors or []), "author_sort": mi.author_sort,
        "series": mi.series, "series_index": mi.series_index if mi.series else None,
        "languages": list(mi.languages or []), "publisher": mi.publisher,
        "tags": list(mi.tags or []), "identifiers": dict(mi.get_identifiers() or {}),
        "pubdate": mi.pubdate.isoformat() if mi.pubdate and mi.pubdate.year > 101 else None,
        "has_cover": bool(mi.cover_data and mi.cover_data[1]),
    }
